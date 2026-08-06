"""Tests for the /health endpoint's Redis check (issue #155)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check
from core.config import settings


@pytest.mark.unit
class TestHealthCheckRedis:
    """Test suite verifying the Redis health check uses settings.redis_url."""

    @pytest.mark.asyncio
    async def test_redis_check_uses_redis_url_not_missing_attrs(self) -> None:
        """The Redis client must be built from settings.redis_url.

        Settings has no redis_host/redis_port fields, so referencing them
        raised an AttributeError that was silently swallowed and reported
        as "unhealthy" regardless of Redis's actual status.
        """
        mock_db = AsyncMock()
        mock_redis_client = MagicMock()

        with patch("redis.Redis.from_url", return_value=mock_redis_client) as mock_from_url:
            result = await health_check(db=mock_db)

        mock_from_url.assert_called_once_with(settings.redis_url, decode_responses=True)
        mock_redis_client.ping.assert_called_once()
        assert result["dependencies"]["redis"] == "healthy"

    @pytest.mark.asyncio
    async def test_redis_check_reports_unhealthy_when_ping_fails(self) -> None:
        """A real Redis outage should still be reported as unhealthy."""
        mock_db = AsyncMock()
        mock_redis_client = MagicMock()
        mock_redis_client.ping.side_effect = ConnectionError("connection refused")

        with (
            patch("redis.Redis.from_url", return_value=mock_redis_client),
            pytest.raises(HTTPException),
        ):
            await health_check(db=mock_db)
