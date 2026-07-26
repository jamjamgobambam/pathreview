"""Reproduction test for issue #155.

api/routes/health.py builds its Redis client from ``settings.redis_host`` /
``settings.redis_port`` (health.py:45-46), but ``Settings`` in core/config.py defines
only ``redis_url`` (config.py:12). Reading the missing attribute raises
``AttributeError``, which health.py's broad ``except Exception`` (health.py:53) swallows,
so ``/health`` falsely reports Redis as "unhealthy" and returns 503 even when Redis is
reachable.

This test asserts the CORRECT contract (Redis reported healthy when reachable) and
therefore FAILS on the current buggy code. It should turn green once health.py reads
``settings.redis_url``, so it doubles as a regression guard.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.database import get_db


async def _fake_db():
    """Stub DB session so the Postgres probe passes and we isolate the Redis probe."""
    db = MagicMock()

    async def _execute(*args, **kwargs):
        return MagicMock()

    db.execute = _execute
    yield db


@pytest.mark.unit
def test_health_reports_redis_healthy_when_reachable():
    """/health must report Redis healthy when Redis is reachable.

    Reproduces #155: currently fails because settings.redis_host does not exist.
    """
    app.dependency_overrides[get_db] = _fake_db
    try:
        # Patch the redis client so no real Redis connection is needed and ping() succeeds.
        # (Covers both possible fix shapes: redis.Redis(...) and redis.Redis.from_url(...).)
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            mock_redis.from_url.return_value.ping.return_value = True

            # No context-manager form -> the startup/init_db event does not run.
            client = TestClient(app)
            response = client.get("/health")

        body = response.json()
        # /health wraps its payload in `detail` on the 503 path; top-level on the 200 path.
        dependencies = body["detail"]["dependencies"] if "detail" in body else body["dependencies"]

        assert dependencies["redis"] == "healthy", (
            "Redis is reachable but /health reports it unhealthy. Root cause: "
            "api/routes/health.py:45-46 reads settings.redis_host / settings.redis_port, "
            "which core/config.py Settings does not define (only redis_url), raising "
            "AttributeError that the broad except-block swallows into a false 'unhealthy'."
        )
    finally:
        app.dependency_overrides.pop(get_db, None)
