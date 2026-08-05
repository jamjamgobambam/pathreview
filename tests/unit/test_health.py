"""Tests for the health check route."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.routes.health import health_check
from core.config import settings


@pytest.mark.unit
class TestHealthCheck:
    """Test the health check route with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_when_dependencies_are_healthy(self):
        db = AsyncMock()
        redis_client = Mock()
        redis_client.ping = Mock()

        with patch("redis.from_url", return_value=redis_client), patch.object(
            settings, "vector_db_url", "http://test-vector-db:8000"
        ):
            result = await health_check(db)

        assert result["status"] == "healthy"
        assert result["dependencies"] == {
            "postgres": "healthy",
            "redis": "healthy",
            "vector_db": "healthy",
        }
        db.execute.assert_awaited_once_with("SELECT 1")
        redis_client.ping.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_health_check_uses_redis_url_from_settings(self):
        db = AsyncMock()
        redis_client = Mock()
        redis_client.ping = Mock()
        redis_url = "redis://test-host:6380/3"

        with patch.object(settings, "redis_url", redis_url), patch.object(
            settings, "vector_db_url", "http://test-vector-db:8000"
        ), patch("redis.from_url", return_value=redis_client) as redis_factory:
            result = await health_check(db)

        redis_factory.assert_called_once_with(redis_url, decode_responses=True)
        redis_client.ping.assert_called_once_with()
        assert result["dependencies"]["redis"] == "healthy"
