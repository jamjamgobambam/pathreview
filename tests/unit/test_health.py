"""Tests for health.py"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import redis
from fastapi import HTTPException

from api.routes.health import health_check
from core.config import settings


@pytest.mark.unit
class TestHealthCheckRedisProbe:
    """Test suite for the Redis dependency probe in the health endpoint."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session that succeeds."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    def test_settings_defines_redis_url_not_host_or_port(self):
        """Test Settings exposes redis_url and not redis_host or redis_port."""
        assert hasattr(settings, "redis_url")
        assert not hasattr(settings, "redis_host")
        assert not hasattr(settings, "redis_port")

    @pytest.mark.asyncio
    async def test_redis_probe_builds_client_from_redis_url(self, mock_db_session):
        """Test the Redis probe builds its client from settings.redis_url."""
        with patch("redis.Redis.from_url") as mock_from_url:
            mock_from_url.return_value = Mock()
            await health_check(db=mock_db_session)

        mock_from_url.assert_called_once_with(
            settings.redis_url,
            decode_responses=True,
        )

    @pytest.mark.asyncio
    async def test_redis_reported_healthy_when_ping_succeeds(self, mock_db_session):
        """Test the Redis dependency is reported healthy when the ping succeeds."""
        with patch("redis.Redis.from_url") as mock_from_url:
            mock_from_url.return_value = Mock()
            result = await health_check(db=mock_db_session)

        assert result["dependencies"]["redis"] == "healthy"

    @pytest.mark.asyncio
    async def test_redis_reported_unhealthy_when_ping_fails(self, mock_db_session):
        """Test the Redis dependency is reported unhealthy when the ping fails."""
        failing_client = Mock()
        failing_client.ping.side_effect = redis.RedisError("connection refused")

        with (
            patch("redis.Redis.from_url", return_value=failing_client),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=mock_db_session)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["dependencies"]["redis"] == "unhealthy"
