"""Unit tests for the health-check route."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.routes.health import health_check
from core.config import settings


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_uses_configured_redis_url() -> None:
    """Verify health check initializes Redis using settings.redis_url."""
    mock_db = AsyncMock()
    mock_redis_instance = Mock()

    with patch("redis.Redis.from_url", return_value=mock_redis_instance) as mock_from_url:
        response = await health_check(mock_db)

        # Verify Redis.from_url was called with settings.redis_url
        mock_from_url.assert_called_once_with(settings.redis_url, decode_responses=True)
        mock_redis_instance.ping.assert_called_once()
        assert response["dependencies"]["redis"] == "healthy"
