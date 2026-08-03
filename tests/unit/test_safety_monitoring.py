"""Tests for monitoring.py."""

from unittest.mock import Mock

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

    def test_get_total_event_count_sums_all_event_types(
        self,
        monitor: SafetyMonitor,
        mock_redis: Mock,
    ) -> None:
        """Test total event count sums all valid event types."""
        mock_redis.zcount.side_effect = [1, 2, 0, 3, 1]

        total = monitor.get_total_event_count(window_hours=1)

        assert total == 7
        assert mock_redis.zcount.call_count == len(SafetyMonitor.VALID_EVENT_TYPES)

    def test_get_total_event_count_returns_zero_when_no_events(
        self,
        monitor: SafetyMonitor,
        mock_redis: Mock,
    ) -> None:
        """Test total count is zero when no events exist."""
        mock_redis.zcount.return_value = 0

        total = monitor.get_total_event_count(window_hours=1)

        assert total == 0
