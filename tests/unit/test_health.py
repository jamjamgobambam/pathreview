"""Tests for the /health endpoint (Issue #68).

The endpoint surfaces `safety_events_last_hour` from
safety.monitoring.SafetyMonitor and degrades to 0 (without failing the whole
health check) when safety counts are unavailable.

Issue: https://github.com/ascherj/pathreview/issues/68
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check
from safety.monitoring import SafetyMonitor


@pytest.mark.unit
class TestHealthSafetyEvents:
    """safety_events_last_hour reflects SafetyMonitor and degrades gracefully."""

    @pytest.fixture
    def mock_db(self):
        """Async mock DB session that satisfies `await db.execute(...)`."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_settings(self):
        """Patch core.config.settings with the attributes health_check uses."""
        with patch("core.config.settings") as settings:
            settings.redis_url = "redis://localhost:6379/0"
            settings.vector_db_url = "http://localhost:8001"
            yield settings

    @pytest.fixture
    def mock_redis_client(self):
        """Patch redis.from_url to return a client whose ping succeeds."""
        with patch("redis.from_url") as from_url:
            client = MagicMock()
            client.ping.return_value = True
            from_url.return_value = client
            yield client

    @pytest.mark.asyncio
    async def test_safety_events_last_hour_reflects_safety_monitor(
        self, mock_db, mock_settings, mock_redis_client
    ):
        """The endpoint surfaces the total SafetyMonitor reports."""
        with patch.object(SafetyMonitor, "get_total_event_count", return_value=7):
            result = await health_check(db=mock_db)

        assert result["safety_events_last_hour"] == 7
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_safety_events_falls_back_to_zero_when_monitor_fails(
        self, mock_db, mock_settings, mock_redis_client
    ):
        """A SafetyMonitor failure degrades the field to 0 without breaking /health."""
        with patch.object(SafetyMonitor, "get_total_event_count", side_effect=Exception("boom")):
            result = await health_check(db=mock_db)

        assert result["safety_events_last_hour"] == 0
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_safety_events_field_present_when_dependencies_down(self, mock_db, mock_settings):
        """When Redis is down the endpoint 503s and the safety field is still present."""
        with (
            patch("redis.from_url", side_effect=ConnectionError("redis is down")),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=mock_db)

        assert exc_info.value.status_code == 503
        detail = exc_info.value.detail
        assert detail["safety_events_last_hour"] == 0
        assert detail["dependencies"]["redis"] == "unhealthy"
