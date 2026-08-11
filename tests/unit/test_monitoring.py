"""Tests for monitoring.py"""

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

    def test_log_event_valid_type_writes_to_redis(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that a valid event type is recorded in the Redis sorted set."""
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        monitor.log_event("pii_detected", {"count": 1})

        mock_redis.zadd.assert_called_once()
        key, member_dict = mock_redis.zadd.call_args[0]
        assert key == "safety:events:pii_detected"
        assert isinstance(member_dict, dict)
        assert len(member_dict) == 1

    def test_log_event_sets_expiry(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Test that the Redis key expiry is set to 24 hours."""
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        monitor.log_event("injection_attempt", {})

        mock_redis.expire.assert_called_once_with("safety:events:injection_attempt", 86400)

    def test_log_event_unknown_type_ignored(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Test that an unknown event type is not written to Redis."""
        mock_redis.zadd = Mock()

        monitor.log_event("not_a_real_event_type", {})

        mock_redis.zadd.assert_not_called()

    def test_log_event_redis_error_handled(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Test that Redis errors during logging are swallowed."""
        mock_redis.zadd = Mock(side_effect=Exception("Redis error"))

        with patch("safety.monitoring.logger"):
            monitor.log_event("pii_detected", {})  # Should not raise

    def test_get_event_count_returns_zero_when_empty(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test count is zero when no events are recorded."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        count = monitor.get_event_count("pii_detected")

        assert count == 0

    def test_get_event_count_returns_current_count(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test count reflects the number of events currently in the window."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=7)

        count = monitor.get_event_count("bias_detected")

        assert count == 7

    def test_get_event_count_prunes_before_counting(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that entries outside the window are pruned before ZCARD is read."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        with patch("time.time", return_value=10_000):
            monitor.get_event_count("rate_limited", window_hours=1)

        mock_redis.zremrangebyscore.assert_called_once()
        key, min_score, max_score = mock_redis.zremrangebyscore.call_args[0]
        assert key == "safety:events:rate_limited"
        assert min_score == 0
        assert max_score == 10_000 - 3600

    def test_get_event_count_respects_custom_window(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that a custom window_hours changes the prune boundary."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        with patch("time.time", return_value=10_000):
            monitor.get_event_count("rate_limited", window_hours=2)

        max_score = mock_redis.zremrangebyscore.call_args[0][2]
        assert max_score == 10_000 - 7200

    def test_get_event_count_redis_error_returns_zero(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that Redis errors during count reads fail safe to zero."""
        mock_redis.zremrangebyscore = Mock(side_effect=Exception("Redis error"))

        with patch("safety.monitoring.logger"):
            count = monitor.get_event_count("pii_detected")

        assert count == 0

    def test_get_total_event_count_sums_all_event_types(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that the total count sums counts across every valid event type."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=2)

        total = monitor.get_total_event_count()

        assert total == 2 * len(SafetyMonitor.VALID_EVENT_TYPES)

    def test_get_total_event_count_zero_when_no_events(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that the total is zero when nothing has been logged."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        assert monitor.get_total_event_count() == 0

    def test_get_total_event_count_partial_redis_failure_fails_safe(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that a Redis error for one event type doesn't crash the aggregate."""
        mock_redis.zremrangebyscore = Mock(side_effect=Exception("Redis error"))
        mock_redis.zcard = Mock(return_value=5)

        with patch("safety.monitoring.logger"):
            total = monitor.get_total_event_count()

        assert total == 0
