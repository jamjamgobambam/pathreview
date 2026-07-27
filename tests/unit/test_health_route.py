"""Tests for the health route."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.routes import health
from safety.monitoring import SafetyMonitor


@pytest.mark.unit
class TestHealthRoute:
    """Test suite for the /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_reports_real_safety_event_count(self):
        """Test /health surfaces real safety event counts from monitoring."""
        # Reproduces issue #68: safety_events_last_hour is hardcoded to 0 and
        # never reads from safety/monitoring.py, so the endpoint reports 0 even
        # when the safety monitor has recorded events.

        # A safety monitor that has recorded 7 events this hour.
        monitor_redis = Mock()
        monitor_redis.get.return_value = "7"  # Redis returns strings
        monitor = SafetyMonitor(monitor_redis)
        recorded = monitor.get_event_count("pii_detected")
        assert recorded == 7

        # Make the health check's own dependency probes pass.
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
            result = await health.health_check(db)

        # Currently FAILS (0 != 7): health.py hardcodes safety_events_last_hour.
        assert result["safety_events_last_hour"] == recorded
