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

    def test_log_event_records_in_sorted_set(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that a valid event is recorded via zadd with a timestamp score."""
        with patch("time.time", return_value=1000.0):
            monitor.log_event("pii_detected", {"field": "email"})

        mock_redis.zadd.assert_called_once()
        call_args = mock_redis.zadd.call_args
        assert call_args[0][0] == "safety:events:pii_detected"
        assert call_args[0][1] == {"1000.0": 1000.0}

    def test_log_event_sets_expiry(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Test that the event key gets a 24h expiry."""
        monitor.log_event("pii_detected", {})

        mock_redis.expire.assert_called_once_with("safety:events:pii_detected", 86400)

    def test_log_event_rejects_unknown_type(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Test unknown event types are dropped without touching Redis."""
        monitor.log_event("not_a_real_event", {})

        mock_redis.zadd.assert_not_called()
        mock_redis.expire.assert_not_called()

    def test_log_event_handles_redis_error(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Test log_event swallows Redis errors instead of raising."""
        mock_redis.zadd = Mock(side_effect=Exception("Redis error"))

        with patch("safety.monitoring.logger"):
            monitor.log_event("pii_detected", {})  # should not raise

    def test_get_event_count_evicts_entries_outside_window(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test get_event_count trims entries older than the window before counting."""
        mock_redis.zcount = Mock(return_value=0)

        with patch("time.time", return_value=10000.0):
            monitor.get_event_count("pii_detected", window_hours=1)

        mock_redis.zremrangebyscore.assert_called_once()
        call_args = mock_redis.zremrangebyscore.call_args
        assert call_args[0][0] == "safety:events:pii_detected"
        assert call_args[0][1] == 0
        # window_start should be 10000 - 3600 = 6400
        assert call_args[0][2] == 6400.0

    def test_get_event_count_returns_zcount_result(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test get_event_count returns the windowed count from Redis."""
        mock_redis.zcount = Mock(return_value=7)

        count = monitor.get_event_count("pii_detected", window_hours=1)

        assert count == 7

    def test_get_event_count_respects_custom_window(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test a custom window_hours changes the eviction cutoff."""
        mock_redis.zcount = Mock(return_value=0)

        with patch("time.time", return_value=10000.0):
            monitor.get_event_count("pii_detected", window_hours=2)

        call_args = mock_redis.zremrangebyscore.call_args
        # window_start should be 10000 - 7200 = 2800
        assert call_args[0][2] == 2800.0

    def test_get_event_count_handles_redis_error(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test get_event_count returns 0 on Redis failure instead of raising."""
        mock_redis.zremrangebyscore = Mock(side_effect=Exception("Redis error"))

        with patch("safety.monitoring.logger"):
            count = monitor.get_event_count("pii_detected", window_hours=1)

        assert count == 0

    def test_get_total_event_count_sums_across_event_types(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test get_total_event_count aggregates counts across all event types."""
        counts_by_key = {
            "safety:events:pii_detected": 3,
            "safety:events:injection_attempt": 2,
            "safety:events:content_filtered": 1,
            "safety:events:bias_detected": 0,
            "safety:events:rate_limited": 4,
        }
        mock_redis.zcount = Mock(side_effect=lambda key, *_args: counts_by_key[key])

        total = monitor.get_total_event_count(window_hours=1)

        assert total == sum(counts_by_key.values())

    def test_get_total_event_count_empty(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Test get_total_event_count is 0 when no events have been logged."""
        mock_redis.zcount = Mock(return_value=0)

        total = monitor.get_total_event_count(window_hours=1)

        assert total == 0
