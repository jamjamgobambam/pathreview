"""Tests for safety/monitoring.py SafetyMonitor."""

from unittest.mock import Mock, patch

import pytest

from safety.monitoring import SafetyMonitor


@pytest.mark.unit
class TestGetTotalEventCount:
    """Test suite for SafetyMonitor.get_total_event_count (Issue #68)."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        return Mock()

    @pytest.fixture
    def monitor(self, mock_redis):
        """Create a SafetyMonitor with a mocked Redis client."""
        return SafetyMonitor(mock_redis)

    def test_sums_counts_across_all_event_types(self, monitor, mock_redis):
        """Total is the sum of the per-event-type counts stored in Redis."""
        counts = {
            "safety:events:pii_detected": "3",
            "safety:events:injection_attempt": "4",
        }
        mock_redis.get.side_effect = counts.get

        assert monitor.get_total_event_count() == 7

    def test_returns_zero_when_no_events(self, monitor, mock_redis):
        """Missing keys (no events logged) yield a total of 0."""
        mock_redis.get.return_value = None

        assert monitor.get_total_event_count() == 0

    def test_queries_every_valid_event_type(self, monitor, mock_redis):
        """Iteration is bounded by VALID_EVENT_TYPES; nothing else is queried."""
        mock_redis.get.return_value = "1"

        assert monitor.get_total_event_count() == len(SafetyMonitor.VALID_EVENT_TYPES)
        assert mock_redis.get.call_count == len(SafetyMonitor.VALID_EVENT_TYPES)
        queried_keys = {call.args[0] for call in mock_redis.get.call_args_list}
        expected_keys = {f"safety:events:{t}" for t in SafetyMonitor.VALID_EVENT_TYPES}
        assert queried_keys == expected_keys

    def test_returns_zero_on_redis_error(self, monitor, mock_redis):
        """Redis failures degrade to 0 instead of raising."""
        mock_redis.get.side_effect = ConnectionError("redis is down")

        assert monitor.get_total_event_count() == 0

    def test_treats_non_integer_values_as_zero(self, monitor, mock_redis):
        """A non-integer value in Redis counts as 0 for that event type only."""

        def fake_get(key):
            if key == "safety:events:pii_detected":
                return "not-a-number"
            return "1"

        mock_redis.get.side_effect = fake_get

        assert monitor.get_total_event_count() == len(SafetyMonitor.VALID_EVENT_TYPES) - 1

    def test_passes_window_hours_to_get_event_count(self, monitor):
        """The window argument is forwarded to each per-type lookup."""
        with patch.object(monitor, "get_event_count", return_value=2) as mock_get:
            total = monitor.get_total_event_count(window_hours=3)

        assert total == 2 * len(SafetyMonitor.VALID_EVENT_TYPES)
        assert mock_get.call_count == len(SafetyMonitor.VALID_EVENT_TYPES)
        for call in mock_get.call_args_list:
            assert call.kwargs["window_hours"] == 3
