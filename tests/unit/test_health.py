"""Tests for api/routes/health.py"""
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheckRedis:
    """Test suite for the /health endpoint's Redis dependency check."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        db = MagicMock()
        db.execute = AsyncMock(return_value=None)
        return db

    @pytest.mark.asyncio
    async def test_redis_healthy_when_reachable(self, mock_db: MagicMock) -> None:
        mock_redis_client = MagicMock()
        mock_redis_client.ping = MagicMock(return_value=True)

        with patch("redis.Redis.from_url", return_value=mock_redis_client):
            try:
                result = await health_check(db=mock_db)
            except HTTPException as exc:
                result = exc.detail

        assert result["dependencies"]["redis"] == "healthy"

    @pytest.mark.asyncio
    async def test_redis_unhealthy_when_unreachable(self, mock_db: MagicMock) -> None:
        with (
            patch("redis.Redis.from_url", side_effect=Exception("Timeout connecting to server")),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=mock_db)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["dependencies"]["redis"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_redis_check_uses_settings_redis_url(self, mock_db: MagicMock) -> None:
        mock_redis_client = MagicMock()
        mock_redis_client.ping = MagicMock(return_value=True)

        with (
            patch("redis.Redis.from_url", return_value=mock_redis_client) as mock_from_url,
            suppress(HTTPException),
        ):
            await health_check(db=mock_db)

        assert mock_from_url.called
        call_args, _ = mock_from_url.call_args
        assert len(call_args) >= 1
        assert isinstance(call_args[0], str)
        assert call_args[0].startswith("redis://")
