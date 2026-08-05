"""Unit tests for the /health endpoint.

Regression coverage for issue #155: the Redis probe previously read
``settings.redis_host`` / ``settings.redis_port``, which do not exist on the
Settings model, raising ``AttributeError``. The probe now uses the existing
``settings.redis_url`` field via ``redis.Redis.from_url``.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.database import get_db


@pytest.fixture
def fake_db():
    """A database session whose ``execute`` succeeds (postgres healthy)."""
    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)
    return db


@pytest.fixture
def client(fake_db):
    """TestClient with the DB dependency overridden so no real DB is needed."""

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_health_uses_redis_url_and_reports_healthy(client):
    """With a reachable Redis, /health returns 200 and redis is healthy.

    This is the core regression test for issue #155: reaching the Redis probe
    must not raise AttributeError, and Redis must be built from redis_url.
    """
    fake_redis = MagicMock()
    fake_redis.ping.return_value = True

    with patch("redis.Redis.from_url", return_value=fake_redis) as from_url:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["dependencies"]["redis"] == "healthy"
    # The probe must be constructed from the existing redis_url setting.
    from_url.assert_called_once()


@pytest.mark.unit
def test_health_reports_redis_unhealthy_when_ping_fails(client):
    """A failing Redis ping degrades status to unhealthy and returns 503."""
    fake_redis = MagicMock()
    fake_redis.ping.side_effect = ConnectionError("redis down")

    with patch("redis.Redis.from_url", return_value=fake_redis):
        response = client.get("/health")

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["dependencies"]["redis"] == "unhealthy"
    assert detail["status"] == "unhealthy"


@pytest.mark.unit
def test_health_does_not_reference_removed_redis_host_fields():
    """Guard against reintroducing the nonexistent redis_host/redis_port fields."""
    from core.config import settings

    assert not hasattr(settings, "redis_host")
    assert not hasattr(settings, "redis_port")
    assert settings.redis_url  # the field the probe should use
