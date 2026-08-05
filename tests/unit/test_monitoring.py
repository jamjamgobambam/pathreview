"""Tests for safety/monitoring.py (SafetyMonitor)."""

from unittest.mock import Mock

import pytest

from safety.monitoring import SafetyMonitor


class FakeRedis:
    """Minimal in-memory Redis stand-in supporting the counter operations used."""

    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key: str, seconds: int) -> None:
        pass

    def get(self, key: str):
        return self.store.get(key)


@pytest.mark.unit
class TestSafetyMonitor:
    """Test suite for SafetyMonitor, focused on get_total_event_count."""

    @pytest.fixture
    def redis(self) -> FakeRedis:
        return FakeRedis()

    @pytest.fixture
    def monitor(self, redis: FakeRedis) -> SafetyMonitor:
        return SafetyMonitor(redis)

    def test_total_is_zero_when_no_events(self, monitor: SafetyMonitor) -> None:
        """With no events recorded, the total is 0 (not an error)."""
        assert monitor.get_total_event_count() == 0

    def test_total_sums_across_event_types(self, monitor: SafetyMonitor) -> None:
        """The total sums counts across all event types, not just one."""
        monitor.log_event("pii_detected", {"field": "email"})
        monitor.log_event("pii_detected", {"field": "phone"})
        monitor.log_event("injection_attempt", {"pattern": "ignore previous"})
        monitor.log_event("rate_limited", {"ip": "1.2.3.4"})

        # 2 pii_detected + 1 injection_attempt + 1 rate_limited = 4
        assert monitor.get_total_event_count() == 4

    def test_total_ignores_unknown_event_types(self, monitor: SafetyMonitor) -> None:
        """Events with unknown types are dropped by log_event and not counted."""
        monitor.log_event("pii_detected", {"field": "email"})
        monitor.log_event("not_a_real_event", {"foo": "bar"})  # rejected

        assert monitor.get_total_event_count() == 1

    def test_total_defaults_to_zero_on_redis_error(self) -> None:
        """A Redis read failure degrades to 0 rather than raising."""
        broken_redis = Mock()
        broken_redis.get = Mock(side_effect=ConnectionError("redis down"))
        monitor = SafetyMonitor(broken_redis)

        # get_event_count swallows the error per key and returns 0, so the sum is 0.
        assert monitor.get_total_event_count() == 0

    def test_single_type_count(self, monitor: SafetyMonitor) -> None:
        """get_event_count returns the count for one event type."""
        monitor.log_event("bias_detected", {"score": 0.9})
        monitor.log_event("bias_detected", {"score": 0.8})

        assert monitor.get_event_count("bias_detected") == 2
        assert monitor.get_event_count("pii_detected") == 0
