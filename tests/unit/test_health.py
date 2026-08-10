"""Tests for the /health endpoint (api/routes/health.py).

Focus: issue #155 — the Redis check must build its client from
``settings.redis_url`` (via ``redis.Redis.from_url``) rather than the
non-existent ``settings.redis_host`` / ``settings.redis_port`` attributes.
Before the fix, the attribute lookup raised ``AttributeError`` inside the
``try`` block, which was swallowed and always reported Redis ``"unhealthy"``.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.database import get_db


@pytest.fixture
def healthy_db():
    """Override get_db with a session whose ``execute`` succeeds."""
    db = Mock()
    db.execute = AsyncMock(return_value=None)

    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    yield db
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client(healthy_db):
    return TestClient(app)


@pytest.mark.unit
class TestHealthRedisCheck:
    """Redis dependency reporting in the /health endpoint."""

    def test_redis_reported_healthy_when_ping_succeeds(self, client):
        """When Redis pings successfully, it is reported healthy (not swallowed)."""
        mock_client = Mock()
        mock_client.ping = Mock(return_value=True)

        with patch("redis.Redis.from_url", return_value=mock_client) as from_url:
            resp = client.get("/health")

        assert resp.status_code == 200
        body = resp.json()
        assert body["dependencies"]["redis"] == "healthy"
        # Regression guard for #155: the client is built from redis_url,
        # never from the non-existent redis_host/redis_port attributes.
        from_url.assert_called_once()
        assert from_url.call_args.args[0].startswith("redis://")

    def test_redis_reported_unhealthy_when_ping_fails(self, client):
        """A real connection failure (not a config bug) surfaces as 503."""
        mock_client = Mock()
        mock_client.ping = Mock(side_effect=ConnectionError("connection refused"))

        with patch("redis.Redis.from_url", return_value=mock_client):
            resp = client.get("/health")

        assert resp.status_code == 503
        body = resp.json()["detail"]
        assert body["dependencies"]["redis"] == "unhealthy"

    def test_health_check_does_not_reference_redis_host(self, client):
        """The endpoint must not touch settings.redis_host (the #155 bug)."""
        from core.config import settings

        assert not hasattr(settings, "redis_host")
        assert not hasattr(settings, "redis_port")

        mock_client = Mock()
        mock_client.ping = Mock(return_value=True)
        with patch("redis.Redis.from_url", return_value=mock_client):
            resp = client.get("/health")

        # No AttributeError leaked through as an unhealthy Redis status.
        assert resp.json()["dependencies"]["redis"] == "healthy"
