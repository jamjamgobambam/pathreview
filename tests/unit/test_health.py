"""Tests for the `/health` endpoint's Redis probe (issue #155).

api/routes/health.py's Redis probe used to reference settings.redis_host and
settings.redis_port, which don't exist on the Settings model (only redis_url
does). That caused an AttributeError which was silently swallowed by the
route's broad `except Exception` block, so the endpoint always reported
Redis "unhealthy" and returned a 503 — even when Redis was actually running
fine.

The fix uses `redis.Redis.from_url(settings.redis_url)`, which correctly
parses the existing connection string. These tests cover: the root cause
no longer exists, a reachable Redis is reported healthy, and a genuinely
unreachable Redis is still correctly reported unhealthy.

See: https://github.com/ascherj/pathreview/issues/155
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check
from core.config import settings


@pytest.mark.unit
class TestHealthCheckRedisFix:
    """Covers issue #155: health check no longer crashes on missing settings fields."""

    def test_settings_has_no_redis_host_or_port_field(self) -> None:
        """Root cause check: Settings only ever defined redis_url, not redis_host/redis_port.

        This confirms the fix went through redis_url rather than adding new
        host/port fields to Settings.
        """
        assert not hasattr(settings, "redis_host")
        assert not hasattr(settings, "redis_port")
        assert hasattr(settings, "redis_url")

    @pytest.mark.asyncio
    async def test_health_check_reports_healthy_when_redis_reachable(self) -> None:
        """A reachable Redis (connected via redis_url) should report healthy, not 503."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True

        with patch("redis.Redis.from_url", return_value=mock_redis_client) as mock_from_url:
            result = await health_check(db=mock_db)

        mock_from_url.assert_called_once_with(settings.redis_url, decode_responses=True)
        assert result["dependencies"]["postgres"] == "healthy"
        assert result["dependencies"]["redis"] == "healthy"
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_reports_unhealthy_when_redis_actually_down(self) -> None:
        """Edge case: a genuine Redis connection failure must still be reported as unhealthy.

        The fix shouldn't make the probe blindly report "healthy" regardless
        of Redis's real state.
        """
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        with (
            patch("redis.Redis.from_url", side_effect=ConnectionError("connection refused")),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=mock_db)

        detail = exc_info.value.detail
        assert exc_info.value.status_code == 503
        assert detail["dependencies"]["postgres"] == "healthy"
        assert detail["dependencies"]["redis"] == "unhealthy"
        assert detail["status"] == "unhealthy"
