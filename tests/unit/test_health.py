"""Tests for api/routes/health.py"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.asyncio
async def test_health_check_reports_redis_healthy_when_reachable() -> None:
    """Test that health_check reports redis as healthy when Redis responds to ping."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()

    with patch("redis.Redis.from_url") as mock_from_url:
        mock_from_url.return_value.ping.return_value = True

        result = await health_check(db=mock_db)

        assert result["dependencies"]["redis"] == "healthy"


@pytest.mark.asyncio
async def test_health_check_reports_redis_unhealthy_when_unreachable() -> None:
    """Test that health_check reports redis as unhealthy when Redis does not respond to ping."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()

    with patch("redis.Redis.from_url") as mock_from_url:
        mock_from_url.return_value.ping.side_effect = ConnectionError("Connection refused")

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db)

        assert exc_info.value.detail["dependencies"]["redis"] == "unhealthy"
