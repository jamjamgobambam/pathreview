"""Tests for safety/monitoring.py"""

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

    def test_log_event_increments_and_expires_key(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that logging a valid event type increments its Redis counter
        and sets the 24h expiry."""
        mock_redis.incr = Mock()
        mock_redis.expire = Mock()

        monitor.log_event("pii_detected", {"field": "email"})

        mock_redis.incr.assert_called_once_with("safety:events:pii_detected")
        mock_redis.expire.assert_called_once_with("safety:events:pii_detected", 86400)

    def test_log_event_rejects_unknown_event_type(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that an unknown event type is ignored, not stored."""
        mock_redis.incr = Mock()

        monitor.log_event("not_a_real_type", {})

        mock_redis.incr.assert_not_called()

    def test_get_event_count_returns_zero_when_key_missing(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that a never-seen event type reports 0, not an error."""
        mock_redis.get = Mock(return_value=None)

        assert monitor.get_event_count("pii_detected") == 0

    def test_get_event_count_returns_stored_value(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that an existing counter value is returned as an int."""
        mock_redis.get = Mock(return_value="4")

        assert monitor.get_event_count("injection_attempt") == 4

    def test_get_event_count_handles_redis_error(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that a Redis error during count lookup degrades to 0."""
        mock_redis.get = Mock(side_effect=ConnectionError("redis down"))

        assert monitor.get_event_count("pii_detected") == 0

    def test_get_total_event_count_sums_all_event_types(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that the total sums counts across every valid event type."""
        counts = {
            "safety:events:pii_detected": "3",
            "safety:events:injection_attempt": "2",
            "safety:events:content_filtered": "0",
            "safety:events:bias_detected": "1",
            "safety:events:rate_limited": "4",
        }
        mock_redis.get = Mock(side_effect=lambda key: counts.get(key))

        assert monitor.get_total_event_count() == 10

    def test_get_total_event_count_zero_when_no_events(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that the total is 0 when no event types have fired."""
        mock_redis.get = Mock(return_value=None)

        assert monitor.get_total_event_count() == 0

    def test_get_total_event_count_ignores_missing_types(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that only some event types firing still sums correctly."""
        mock_redis.get = Mock(
            side_effect=lambda key: "5" if key == "safety:events:pii_detected" else None
        )

        assert monitor.get_total_event_count() == 5

    def test_get_total_event_count_survives_partial_redis_errors(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that a Redis error on one event type doesn't take down the
        total -- get_event_count already swallows per-key errors, so the
        aggregate degrades rather than raising."""

        def flaky_get(key: str) -> str | None:
            if key == "safety:events:pii_detected":
                raise ConnectionError("redis down")
            if key == "safety:events:bias_detected":
                return "2"
            return None

        mock_redis.get = Mock(side_effect=flaky_get)

        assert monitor.get_total_event_count() == 2
