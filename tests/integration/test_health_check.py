"""Reproduction test for issue #155.

Bug: ``api/routes/health.py`` builds its Redis probe from ``settings.redis_host``
and ``settings.redis_port``, but ``core/config.py``'s ``Settings`` only defines
``redis_url`` -- no ``redis_host`` / ``redis_port``. Accessing ``settings.redis_host``
raises ``AttributeError``, which the endpoint's ``try/except`` swallows and reports
Redis as ``"unhealthy"``, forcing ``GET /health`` to return HTTP 503 even when Redis
is actually running.

This test hits the real ``/health`` endpoint and asserts that Redis is reported
healthy when the local Redis container is up. It FAILS on the current (buggy) code
and should PASS once the health check reads Redis connection details that exist on
``Settings``. It is fix-agnostic: it does not care whether the fix parses
``redis_url`` or adds explicit ``redis_host``/``redis_port`` fields.

The database probe is stubbed out so this test isolates the Redis behaviour and is
not affected by the separate DB-probe issue (#154).

Requires the local Redis container to be running: ``docker compose up -d``.
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.database import get_db


async def _fake_db() -> AsyncGenerator[AsyncMock, None]:
    """Yield a stub DB session so the Postgres probe passes and only Redis is tested."""
    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)
    yield db


@pytest.mark.integration
def test_health_reports_redis_healthy_when_redis_is_up() -> None:
    app.dependency_overrides[get_db] = _fake_db
    try:
        client = TestClient(app)
        response = client.get("/health")
        body = response.json()
        # Healthy -> body is the status dict; unhealthy -> wrapped under "detail".
        dependencies = body.get("dependencies") or body.get("detail", {}).get("dependencies", {})
        assert dependencies.get("redis") == "healthy", (
            f"Redis reported as {dependencies.get('redis')!r} (issue #155). "
            f"Full response: {body}"
        )
    finally:
        app.dependency_overrides.pop(get_db, None)
