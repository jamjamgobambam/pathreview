"""Tests for api/routes/health.py

Covers issue #68 (ascherj/pathreview): /health must surface a real
safety_events_last_hour count sourced from SafetyMonitor/Redis instead of a
hardcoded 0.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check
from safety.monitoring import SafetyMonitor


class FakeRedis:
    """Minimal in-memory stand-in for redis.Redis.

    A bare MagicMock can't track state; SafetyMonitor.log_event/get_event_count
    rely on real incr/get semantics, so this fake backs them with a dict.
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


class BrokenRedis(FakeRedis):
    """Fake Redis client that always fails, for degraded-mode tests."""

    def ping(self):
        raise ConnectionError("redis unavailable")

    def get(self, key):
        raise ConnectionError("redis unavailable")


@pytest.mark.unit
class TestHealthCheckSafetyEventCount:
    """Tests for issue #68."""

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
            redis_url="redis://localhost:6379/0",
            vector_db_url="http://localhost:8001",
        )

    def test_safety_monitor_tracks_events_correctly(self, mock_redis):
        """SafetyMonitor's Redis-backed counting works in isolation."""
        monitor = SafetyMonitor(mock_redis)

        monitor.log_event("pii_detected", {"field": "email"})
        monitor.log_event("pii_detected", {"field": "phone"})

        assert monitor.get_event_count("pii_detected") == 2

    @pytest.mark.asyncio
    async def test_health_check_reports_real_safety_event_count(
        self, mock_db_session, mock_redis, fake_settings
    ):
        """/health reflects real safety events logged via SafetyMonitor.

        Regression test for #68: health_check() used to hardcode
        safety_events_last_hour to 0 regardless of real Redis state.
        """
        monitor = SafetyMonitor(mock_redis)
        monitor.log_event("pii_detected", {"field": "email"})
        monitor.log_event("pii_detected", {"field": "phone"})
        real_count = monitor.get_event_count("pii_detected")
        assert real_count == 2  # confirm the events were really logged

        with (
            patch("redis.Redis.from_url", return_value=mock_redis),
            patch("core.config.settings", fake_settings),
        ):
            result = await health_check(db=mock_db_session)

        assert result["safety_events_last_hour"] == real_count

    @pytest.mark.asyncio
    async def test_health_check_aggregates_across_event_types(
        self, mock_db_session, mock_redis, fake_settings
    ):
        """Events across different types are summed into one total."""
        monitor = SafetyMonitor(mock_redis)
        monitor.log_event("pii_detected", {})
        monitor.log_event("bias_detected", {})
        monitor.log_event("bias_detected", {})
        monitor.log_event("rate_limited", {})

        with (
            patch("redis.Redis.from_url", return_value=mock_redis),
            patch("core.config.settings", fake_settings),
        ):
            result = await health_check(db=mock_db_session)

        assert result["safety_events_last_hour"] == 4

    @pytest.mark.asyncio
    async def test_health_check_defaults_to_zero_with_no_events(
        self, mock_db_session, mock_redis, fake_settings
    ):
        """No safety events logged -> count is 0, not an error."""
        with (
            patch("redis.Redis.from_url", return_value=mock_redis),
            patch("core.config.settings", fake_settings),
        ):
            result = await health_check(db=mock_db_session)

        assert result["safety_events_last_hour"] == 0

    @pytest.mark.asyncio
    async def test_health_check_degrades_gracefully_when_redis_unavailable(
        self, mock_db_session, fake_settings
    ):
        """Redis errors during the safety count shouldn't crash /health --
        it should degrade the same way the endpoint already does for its
        other dependencies (mark unhealthy, return 503 with details)."""
        with (
            patch("redis.Redis.from_url", return_value=BrokenRedis()),
            patch("core.config.settings", fake_settings),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=mock_db_session)

        assert exc_info.value.detail["safety_events_last_hour"] == 0
        assert exc_info.value.detail["dependencies"]["redis"] == "unhealthy"
