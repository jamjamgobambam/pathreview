"""Tests for api/routes/health.py"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint."""

    @pytest.mark.asyncio
    async def test_redis_check_healthy_using_redis_url(self) -> None:
        """Covers the fix for issue #155.

        health.py now builds the Redis client from settings.redis_url,
        using redis.Redis.from_url, instead of the missing redis_host
        and redis_port fields. When Redis responds to ping, the health
        check should report redis as healthy.
        """
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=None)

        mock_redis_client = MagicMock()
        mock_redis_client.ping = MagicMock(return_value=True)

        with patch("redis.Redis.from_url", return_value=mock_redis_client) as mock_from_url:
            result = await health_check(db=mock_db)

        mock_from_url.assert_called_once()
        assert result["dependencies"]["redis"] == "healthy"

    @pytest.mark.asyncio
    async def test_redis_check_unhealthy_when_ping_fails(self) -> None:
        """Redis check should still report unhealthy, not crash, when
        Redis itself is unreachable."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=None)

        mock_redis_client = MagicMock()
        mock_redis_client.ping = MagicMock(side_effect=ConnectionError("refused"))

        with (
            patch("redis.Redis.from_url", return_value=mock_redis_client),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=mock_db)

        detail = exc_info.value.detail
        assert detail["dependencies"]["redis"] == "unhealthy"
