"""Tests for issue #155: health check references settings.redis_host,
which does not exist on Settings.

api/routes/health.py originally built its Redis client from
settings.redis_host/settings.redis_port, but Settings (core/config.py) only
defines redis_url. That AttributeError was swallowed by a bare except, so
Redis was unconditionally reported "unhealthy" regardless of its real state.
The fix builds the client from redis_url via redis.Redis.from_url(...).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.routes.health import health_check
from core.config import Settings


@pytest.mark.unit
class TestHealthRedisConfig:
    """Settings/health.py field-mismatch coverage for issue #155."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session that succeeds on SELECT 1."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    def test_settings_has_no_redis_host_field(self) -> None:
        """Settings only exposes redis_url; redis_host/redis_port do not exist.

        Documents the root cause: any code path (like the old health.py) that
        reads settings.redis_host or settings.redis_port will hit an
        AttributeError, since Settings only ever defined redis_url.
        """
        settings = Settings()

        assert hasattr(settings, "redis_url")
        assert not hasattr(settings, "redis_host")
        assert not hasattr(settings, "redis_port")

    @pytest.mark.asyncio
    async def test_health_check_reports_redis_healthy_when_ping_succeeds(
        self, mock_db_session
    ) -> None:
        """health_check() builds its Redis client from redis_url and reports
        "healthy" when ping() succeeds, proving the probe reflects Redis's
        real status instead of always failing on the removed redis_host field."""
        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True

        with patch("redis.Redis.from_url", return_value=mock_redis_client) as mock_from_url:
            result = await health_check(db=mock_db_session)

        assert result["dependencies"]["redis"] == "healthy"
        assert result["status"] == "healthy"
        mock_from_url.assert_called_once()
        assert mock_from_url.call_args.args[0] == Settings().redis_url

    @pytest.mark.asyncio
    async def test_health_check_reports_redis_unhealthy_when_ping_fails(
        self, mock_db_session
    ) -> None:
        """When Redis is unreachable, health_check() still reports "unhealthy"
        and a 503 -- the fix must not turn a real outage into a crash."""
        mock_redis_client = MagicMock()
        mock_redis_client.ping.side_effect = ConnectionError("connection refused")

        with (
            patch("redis.Redis.from_url", return_value=mock_redis_client),
            pytest.raises(Exception) as exc_info,
        ):
            await health_check(db=mock_db_session)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["dependencies"]["redis"] == "unhealthy"
