"""Tests for api/routes/health.py"""

from typing import cast
from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session that succeeds."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_redis_health_check_uses_redis_url(self, mock_db_session: AsyncMock) -> None:
        """Test that Redis health check connects via settings.redis_url,
        not the nonexistent settings.redis_host/redis_port fields."""
        with patch("redis.Redis.from_url") as mock_from_url:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_from_url.return_value = mock_redis_instance

            result = await health_check(db=mock_db_session)

        assert result["dependencies"]["redis"] == "healthy"
        mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_health_check_reports_unhealthy_on_connection_failure(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test that a genuine Redis connection failure is still reported correctly."""
        from fastapi import HTTPException

        with patch("redis.Redis.from_url") as mock_from_url:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = ConnectionError("connection refused")
            mock_from_url.return_value = mock_redis_instance

            with pytest.raises(HTTPException) as exc_info:
                await health_check(db=mock_db_session)

        assert exc_info.value.status_code == 503
        detail = cast("dict", exc_info.value.detail)
        assert detail["dependencies"]["redis"] == "unhealthy"
