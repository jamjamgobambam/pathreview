"""Tests for the /health endpoint's dependency probes."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check
from core.config import Settings, settings


@pytest.mark.unit
class TestHealthCheckRedisProbe:
    """Test suite for the Redis dependency probe in the health endpoint."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session whose probe succeeds."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def healthy_redis(self):
        """Create a mock Redis client that responds to ping."""
        client = Mock()
        client.ping = Mock(return_value=True)
        return client

    def test_settings_defines_redis_url_not_host_port(self):
        """Settings models Redis as a URL, so the probe must not read host/port.

        Guards against the config/consumer drift that caused issue #155.
        """
        settings = Settings()

        assert hasattr(settings, "redis_url")
        assert not hasattr(settings, "redis_host")
        assert not hasattr(settings, "redis_port")

    @pytest.mark.asyncio
    async def test_redis_healthy_when_ping_succeeds(self, mock_db_session, healthy_redis):
        """A reachable Redis is reported healthy.

        Regression test for #155: before the fix the probe raised AttributeError on
        settings.redis_host and reported Redis unhealthy even when it was reachable.
        """
        with patch("redis.Redis.from_url", return_value=healthy_redis):
            result = await health_check(db=mock_db_session)

        assert result["dependencies"]["redis"] == "healthy"
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_redis_probe_uses_configured_url(self, mock_db_session, healthy_redis):
        """The probe builds its client from settings.redis_url."""
        with patch("redis.Redis.from_url", return_value=healthy_redis) as mock_from_url:
            await health_check(db=mock_db_session)

        mock_from_url.assert_called_once()
        assert mock_from_url.call_args.args[0] == settings.redis_url

    @pytest.mark.asyncio
    async def test_unreachable_redis_returns_503(self, mock_db_session):
        """A genuine Redis outage is still detected and surfaced as 503.

        Confirms the fix does not mask real connection failures.
        """
        failing_redis = Mock()
        failing_redis.ping = Mock(side_effect=ConnectionError("connection refused"))

        with (
            patch("redis.Redis.from_url", return_value=failing_redis),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=mock_db_session)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["dependencies"]["redis"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_all_dependencies_healthy(self, mock_db_session, healthy_redis):
        """With every probe succeeding the endpoint reports overall health."""
        with patch("redis.Redis.from_url", return_value=healthy_redis):
            result = await health_check(db=mock_db_session)

        assert result["status"] == "healthy"
        assert result["dependencies"]["postgres"] == "healthy"
        assert result["dependencies"]["redis"] == "healthy"
        assert result["dependencies"]["vector_db"] == "healthy"
