"""Tests for api/routes/health.py

These tests reproduce issue #68 (ascherj/pathreview): the /health endpoint
returns service status but never surfaces real safety metrics. It hardcodes
`safety_events_last_hour` to 0 instead of reading the actual count from
SafetyMonitor/Redis.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from api.routes.health import health_check
from safety.monitoring import SafetyMonitor


class FakeRedis:
    """Minimal in-memory stand-in for redis.Redis.

    A bare MagicMock won't do here: SafetyMonitor.log_event/get_event_count
    rely on incr/get actually tracking state (real redis-py returns ints from
    incr() and str-or-None from get()). This fake mirrors that behavior so
    the test exercises real counting logic instead of mocked-away plumbing.
    """

    def __init__(self):
        self._store: dict[str, int] = {}

    def incr(self, key):
        self._store[key] = self._store.get(key, 0) + 1
        return self._store[key]

    def get(self, key):
        value = self._store.get(key)
        return str(value) if value is not None else None

    def expire(self, key, seconds):
        return True

    def ping(self):
        return True


@pytest.mark.unit
class TestHealthCheckSafetyEventCount:
    """Reproduction tests for issue #68."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session (mirrors other unit tests)."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_redis(self):
        """Create a fake Redis client that actually tracks counts."""
        return FakeRedis()

    @pytest.fixture
    def fake_settings(self):
        """Minimal stand-in for core.config.settings used by health_check."""
        return SimpleNamespace(
            redis_host="localhost",
            redis_port=6379,
            vector_db_url="http://localhost:8001",
        )

    def test_safety_monitor_tracks_events_correctly(self, mock_redis):
        """Sanity check: SafetyMonitor itself works fine in isolation.

        This confirms the Redis-backed counting logic in
        safety/monitoring.py is not the problem -- the bug lives
        elsewhere (see test below).
        """
        monitor = SafetyMonitor(mock_redis)

        monitor.log_event("pii_detected", {"field": "email"})
        monitor.log_event("pii_detected", {"field": "phone"})

        assert monitor.get_event_count("pii_detected") == 2

    @pytest.mark.asyncio
    async def test_health_check_ignores_real_safety_event_count(
        self, mock_db_session, mock_redis, fake_settings
    ):
        """Reproduces #68.

        Even when real safety events have been logged via SafetyMonitor,
        GET /health always reports safety_events_last_hour == 0, because
        health_check() hardcodes the field instead of calling
        SafetyMonitor.get_event_count().

        This test is expected to FAIL until the endpoint is fixed to read
        the real count.
        """
        monitor = SafetyMonitor(mock_redis)
        monitor.log_event("pii_detected", {"field": "email"})
        monitor.log_event("pii_detected", {"field": "phone"})
        real_count = monitor.get_event_count("pii_detected")
        assert real_count == 2  # confirm the events were really logged

        with (
            patch("redis.Redis", return_value=mock_redis),
            patch("core.config.settings", fake_settings),
        ):
            result = await health_check(db=mock_db_session)

        assert result["safety_events_last_hour"] == real_count, (
            "health_check() hardcodes safety_events_last_hour to 0 and never "
            "calls SafetyMonitor.get_event_count() (see issue #68)"
        )
