"""Unit tests for the health-check route."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.routes.health import health_check
from core.config import settings


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_uses_configured_redis_host_and_port() -> None:
    """The Redis probe should use the host and port exposed by Settings."""
    db = AsyncMock()
    redis_client = Mock()

    with patch("redis.Redis", return_value=redis_client) as redis_class:
        result = await health_check(db)

    redis_class.assert_called_once_with(
        host=settings.redis_host,
        port=settings.redis_port,
        db=0,
        decode_responses=True,
    )
    redis_client.ping.assert_called_once_with()
    assert result["status"] == "healthy"
    assert result["dependencies"]["redis"] == "healthy"
