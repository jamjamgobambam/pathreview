"""Tests for safety/monitoring.py"""

from unittest.mock import Mock, patch

import pytest

from safety.monitoring import SafetyMonitor


@pytest.mark.unit
class TestSafetyMonitor:
    """Test suite for SafetyMonitor."""

    @pytest.fixture
    def mock_redis(self) -> Mock:
        """Create a mock Redis client."""
        return Mock()

    @pytest.fixture
    def monitor(self, mock_redis: Mock) -> SafetyMonitor:
        """Create a SafetyMonitor instance with mocked Redis."""
        return SafetyMonitor(mock_redis)

    def test_total_event_count_sums_all_types(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test total count sums counts across all valid event types."""
        counts = {
            "safety:events:pii_detected": "2",
            "safety:events:injection_attempt": "1",
            "safety:events:content_filtered": "3",
            "safety:events:bias_detected": "0",
            "safety:events:rate_limited": "4",
        }
        mock_redis.get = Mock(side_effect=lambda key: counts.get(key))

        total = monitor.get_total_event_count()

        assert total == 10

    def test_total_event_count_zero_when_empty(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test total count is zero when no counters are set in Redis."""
        mock_redis.get = Mock(return_value=None)

        total = monitor.get_total_event_count()

        assert total == 0

    def test_total_event_count_only_counts_valid_types(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test total count queries exactly the keys for VALID_EVENT_TYPES."""
        mock_redis.get = Mock(return_value=None)

        monitor.get_total_event_count()

        queried_keys = {call.args[0] for call in mock_redis.get.call_args_list}
        expected_keys = {
            f"safety:events:{event_type}" for event_type in SafetyMonitor.VALID_EVENT_TYPES
        }
        assert queried_keys == expected_keys

    def test_total_event_count_resilient_to_per_type_error(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test total count keeps summing other types if one type's lookup errors."""

        def get_side_effect(key: str) -> str:
            if key == "safety:events:pii_detected":
                raise Exception("Redis error")
            return "5"

        mock_redis.get = Mock(side_effect=get_side_effect)

        with patch("safety.monitoring.logger"):
            total = monitor.get_total_event_count()

        # 5 for each of the remaining 4 valid event types; pii_detected contributes 0
        assert total == 20
