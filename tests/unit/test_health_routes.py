"""
tests/unit/test_health_routes.py

Tests for the /health endpoint, specifically covering the Redis
configuration bug (issue #155): settings.redis_host/redis_port
did not exist, causing the health check to report Redis as
unhealthy on every request regardless of Redis's actual state.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.database import get_db


@pytest.fixture
def client() -> TestClient:
    """TestClient with the get_db dependency overridden to avoid needing a real database."""

    async def override_get_db():
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=None)
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_check_reports_redis_healthy_when_ping_succeeds(client: TestClient) -> None:
    """
    Regression test for issue #155.

    Before the fix, the Redis check constructed redis.Redis(host=settings.redis_host, ...),
    but Settings only defines redis_url — so this always raised AttributeError and reported
    redis as 'unhealthy', even when Redis itself was working fine.
    """
    mock_redis_client = MagicMock()
    mock_redis_client.ping.return_value = True

    with patch("redis.Redis.from_url", return_value=mock_redis_client) as mock_from_url:
        response = client.get("/health")

    body = response.json()
    detail = body.get("detail", body)
    assert detail["dependencies"]["redis"] == "healthy"

    # Confirm the fix actually used the configured redis_url, not host/port kwargs.
    mock_from_url.assert_called_once()


def test_health_check_reports_redis_unhealthy_when_ping_fails(client):
    """A genuine Redis connection failure should still be reported as unhealthy."""
    with patch("redis.Redis.from_url", side_effect=ConnectionError("connection refused")):
        response = client.get("/health")

    body = response.json()
    detail = body.get("detail", body)
    assert detail["dependencies"]["redis"] == "unhealthy"