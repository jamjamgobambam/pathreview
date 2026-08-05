"""Unit tests for the /health endpoint's Redis check (issue #155).

api/routes/health.py used to build its Redis probe from settings.redis_host
and settings.redis_port, which don't exist on Settings (core/config.py only
defines redis_url). The fix builds the client from settings.redis_url via
redis.Redis.from_url(). These tests call health_check() directly (bypassing
FastAPI's dependency injection and startup events) so they stay Docker-free,
matching the "unit: no external dependencies" marker.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check
from core.config import settings


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_builds_redis_client_from_redis_url():
    mock_db = AsyncMock()
    mock_redis_client = MagicMock()

    with patch("redis.Redis.from_url", return_value=mock_redis_client) as mock_from_url:
        result = await health_check(db=mock_db)

    mock_from_url.assert_called_once_with(settings.redis_url, decode_responses=True)
    mock_redis_client.ping.assert_called_once()
    assert result["dependencies"]["redis"] == "healthy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_reports_redis_unhealthy_when_ping_fails():
    mock_db = AsyncMock()
    mock_redis_client = MagicMock()
    mock_redis_client.ping.side_effect = ConnectionError("connection refused")

    with (
        patch("redis.Redis.from_url", return_value=mock_redis_client),
        pytest.raises(HTTPException) as exc_info,
    ):
        await health_check(db=mock_db)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["dependencies"]["redis"] == "unhealthy"
