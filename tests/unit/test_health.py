"""Tests for the health check route."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import health
from core.config import settings


@pytest.mark.unit
def test_health_check_uses_configured_redis_url() -> None:
    """The health route should probe Redis via the configured URL setting."""
    app = FastAPI()
    app.include_router(health.router)

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=None)
    app.dependency_overrides[health.get_db] = lambda: mock_db

    mock_redis_client = Mock()
    mock_redis_client.ping = Mock(return_value=True)

    with patch("redis.Redis.from_url", return_value=mock_redis_client) as mock_from_url:
        client = TestClient(app)
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["dependencies"]["redis"] == "healthy"
    mock_from_url.assert_called_once_with(settings.redis_url, decode_responses=True)
    mock_redis_client.ping.assert_called_once()
