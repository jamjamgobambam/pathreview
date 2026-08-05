"""Tests for monitoring.py"""

from unittest.mock import Mock

import pytest

from safety.monitoring import SafetyMonitor


@pytest.mark.unit
class TestSafetyMonitorGetTotalEventCount:
    """Test suite for SafetyMonitor.get_total_event_count."""

    @pytest.fixture
    def mock_redis(self) -> Mock:
        """Create a mock Redis client."""
        return Mock()

    @pytest.fixture
    def monitor(self, mock_redis: Mock) -> SafetyMonitor:
        """Create a SafetyMonitor instance with mocked Redis."""
        return SafetyMonitor(mock_redis)

    def test_sums_counts_across_all_event_types(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Total should be the sum of every event type's count."""
        counts = {
            "safety:events:pii_detected": "5",
            "safety:events:injection_attempt": "3",
            "safety:events:content_filtered": "2",
            "safety:events:bias_detected": "0",
            "safety:events:rate_limited": "1",
        }
        mock_redis.get = Mock(side_effect=lambda key: counts.get(key))

        total = monitor.get_total_event_count()

        assert total == 11

    def test_returns_zero_when_no_events_recorded(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """No keys in Redis (None for every type) should total 0."""
        mock_redis.get = Mock(return_value=None)

        total = monitor.get_total_event_count()

        assert total == 0

    def test_only_some_event_types_have_counts(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Missing keys for some event types should contribute 0, not error."""
        counts = {"safety:events:pii_detected": "4"}
        mock_redis.get = Mock(side_effect=lambda key: counts.get(key))

        total = monitor.get_total_event_count()

        assert total == 4

    def test_redis_failure_degrades_to_zero_for_that_type(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """A Redis error on one type must not crash the total; it contributes 0."""
        mock_redis.get = Mock(side_effect=ConnectionError("redis unavailable"))

        total = monitor.get_total_event_count()

        assert total == 0

    def test_covers_every_valid_event_type(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Every VALID_EVENT_TYPES key should be queried exactly once."""
        mock_redis.get = Mock(return_value=None)

        monitor.get_total_event_count()

        queried_keys = {call.args[0] for call in mock_redis.get.call_args_list}
        expected_keys = {
            f"safety:events:{event_type}" for event_type in SafetyMonitor.VALID_EVENT_TYPES
        }
        assert queried_keys == expected_keys
