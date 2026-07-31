"""Unit tests for the health-check route."""

from typing import Any, cast
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status

from api.routes.health import health_check
from core.config import settings


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_reports_redis_healthy_when_ping_succeeds() -> None:
    """Report Redis as healthy when the configured instance responds to ping."""
    db = AsyncMock()
    redis_client = Mock()

    with patch("redis.Redis.from_url", return_value=redis_client) as from_url:
        result = await health_check(db)

    from_url.assert_called_once_with(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=1,
    )
    redis_client.ping.assert_called_once_with()
    assert result["dependencies"]["redis"] == "healthy"
    assert result["status"] == "healthy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_reports_redis_unhealthy_when_ping_fails() -> None:
    """Return 503 with an unhealthy Redis status when ping raises an error."""
    db = AsyncMock()
    redis_client = Mock()
    redis_client.ping.side_effect = ConnectionError("Redis is unavailable")

    with (
        patch("redis.Redis.from_url", return_value=redis_client),
        pytest.raises(HTTPException) as exc_info,
    ):
        await health_check(db)

    detail = cast(dict[str, Any], exc_info.value.detail)
    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert detail["dependencies"]["redis"] == "unhealthy"
    assert detail["status"] == "unhealthy"
