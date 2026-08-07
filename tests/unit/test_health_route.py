"""Tests for the health route."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.routes import health


@pytest.mark.unit
class TestHealthRoute:
    """Test suite for the /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_reports_safety_event_count_from_monitor(self):
        """Test /health surfaces the total safety event count from the monitor."""
        # Issue #68: the endpoint must report real safety metrics, not a hardcoded 0.
        # The monitor is injected via Depends, so we hand in a fake reporting 7 events.
        monitor = Mock()
        monitor.get_total_event_count.return_value = 7

        # Make the health check's own dependency probes pass so it returns 200.
        db = Mock()
        db.execute = AsyncMock()

        fake_health_redis = Mock()
        fake_health_redis.ping.return_value = True

        fake_settings = SimpleNamespace(
            redis_host="localhost",
            redis_port=6379,
            vector_db_url="http://localhost:8001",
        )

        with (
            patch("redis.Redis", return_value=fake_health_redis),
            patch("core.config.settings", fake_settings),
        ):
            result = await health.health_check(db=db, monitor=monitor)

        assert result["safety_events_last_hour"] == 7
