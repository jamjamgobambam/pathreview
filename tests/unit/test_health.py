"""Tests for api/routes/health.py"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheckRedis:
    """Test suite for the Redis portion of the /health endpoint (issue #155)."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create a mock async database session that never raises."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_redis_healthy_reports_healthy_status(self, mock_db: AsyncMock) -> None:
        """Redis reachable -> health check reports 'healthy', no AttributeError."""
        mock_redis_client = Mock()
        mock_redis_client.ping = Mock(return_value=True)

        with patch("redis.Redis.from_url", return_value=mock_redis_client) as mock_from_url:
            result = await health_check(db=mock_db)

        assert result["dependencies"]["redis"] == "healthy"
        # Confirms the fix uses settings.redis_url, not the nonexistent redis_host/redis_port
        mock_from_url.assert_called_once()
        args, kwargs = mock_from_url.call_args
        assert args[0].startswith("redis://")

    @pytest.mark.asyncio
    async def test_redis_unreachable_reports_unhealthy_without_crashing(
        self, mock_db: AsyncMock
    ) -> None:
        """Redis down -> health check reports 'unhealthy' and raises 503, not AttributeError."""
        with (
            patch("redis.Redis.from_url", side_effect=ConnectionError("Connection refused")),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=mock_db)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["dependencies"]["redis"] == "unhealthy"
