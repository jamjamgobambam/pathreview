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

    # --- log_event ---

    def test_log_event_valid_type_calls_zadd(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that logging a valid event type writes to Redis via zadd."""
        mock_redis.zadd = Mock()
        mock_redis.zremrangebyscore = Mock()
        mock_redis.expire = Mock()

        with patch("time.time", return_value=1000.0):
            monitor.log_event("pii_detected", {"id": "abc"})

        mock_redis.zadd.assert_called_once()
        call_args = mock_redis.zadd.call_args
        key = call_args[0][0]
        assert key == "safety:events:pii_detected"

    def test_log_event_unknown_type_does_not_call_redis(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that an unknown event type is rejected before touching Redis."""
        mock_redis.zadd = Mock()

        monitor.log_event("not_a_real_event_type", {})

        mock_redis.zadd.assert_not_called()

    def test_log_event_trims_old_entries(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Test that log_event trims entries older than the retention window."""
        mock_redis.zadd = Mock()
        mock_redis.zremrangebyscore = Mock()
        mock_redis.expire = Mock()

        with patch("time.time", return_value=100000.0):
            monitor.log_event("rate_limited", {})

        mock_redis.zremrangebyscore.assert_called_once()
        call_args = mock_redis.zremrangebyscore.call_args
        key = call_args[0][0]
        assert key == "safety:events:rate_limited"
        # cutoff should be now - RETENTION_SECONDS
        cutoff = call_args[0][2]
        assert cutoff == pytest.approx(100000.0 - SafetyMonitor.RETENTION_SECONDS)

    def test_log_event_sets_expiry(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Test that log_event sets a key expiry as a backstop."""
        mock_redis.zadd = Mock()
        mock_redis.zremrangebyscore = Mock()
        mock_redis.expire = Mock()

        monitor.log_event("bias_detected", {})

        mock_redis.expire.assert_called_once()
        call_args = mock_redis.expire.call_args
        assert call_args[0][0] == "safety:events:bias_detected"
        assert call_args[0][1] == SafetyMonitor.RETENTION_SECONDS

    def test_log_event_redis_error_handled_gracefully(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that a Redis failure during log_event doesn't raise."""
        mock_redis.zadd = Mock(side_effect=Exception("Redis down"))

        # Should not raise
        monitor.log_event("injection_attempt", {})

    # --- get_event_count ---

    def test_get_event_count_uses_zcount_with_window(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that get_event_count queries Redis with the correct time window."""
        mock_redis.zcount = Mock(return_value=5)

        with patch("time.time", return_value=10000.0):
            count = monitor.get_event_count("pii_detected", window_hours=1)

        assert count == 5
        mock_redis.zcount.assert_called_once()
        call_args = mock_redis.zcount.call_args
        key, window_start, now = call_args[0]
        assert key == "safety:events:pii_detected"
        assert now == 10000.0
        assert window_start == pytest.approx(10000.0 - 3600)

    def test_get_event_count_respects_custom_window(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that a custom window_hours changes the query window."""
        mock_redis.zcount = Mock(return_value=2)

        with patch("time.time", return_value=10000.0):
            monitor.get_event_count("rate_limited", window_hours=3)

        call_args = mock_redis.zcount.call_args
        window_start = call_args[0][1]
        assert window_start == pytest.approx(10000.0 - (3 * 3600))

    def test_get_event_count_no_events_returns_zero(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that zero events in the window returns 0."""
        mock_redis.zcount = Mock(return_value=0)

        count = monitor.get_event_count("content_filtered")

        assert count == 0

    def test_get_event_count_redis_error_returns_zero(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that a Redis failure during get_event_count returns 0, not a raise."""
        mock_redis.zcount = Mock(side_effect=Exception("Redis down"))

        count = monitor.get_event_count("pii_detected")

        assert count == 0

    def test_get_event_count_is_int(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Test that get_event_count always returns an int."""
        mock_redis.zcount = Mock(return_value=7)

        count = monitor.get_event_count("bias_detected")

        assert isinstance(count, int)

    # --- get_total_event_count ---

    def test_get_total_event_count_sums_across_event_types(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that get_total_event_count sums counts from every valid event type."""
        # Each event type key gets queried once; return 1 for each of the 5 types
        mock_redis.zcount = Mock(return_value=1)

        total = monitor.get_total_event_count(window_hours=1)

        assert total == len(SafetyMonitor.VALID_EVENT_TYPES)
        assert mock_redis.zcount.call_count == len(SafetyMonitor.VALID_EVENT_TYPES)

    def test_get_total_event_count_zero_when_no_events(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that get_total_event_count returns 0 when nothing has happened."""
        mock_redis.zcount = Mock(return_value=0)

        total = monitor.get_total_event_count()

        assert total == 0

    def test_get_total_event_count_mixed_counts(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that get_total_event_count correctly sums differing per-type counts."""
        counts_by_key = {
            "safety:events:pii_detected": 3,
            "safety:events:injection_attempt": 0,
            "safety:events:content_filtered": 2,
            "safety:events:bias_detected": 1,
            "safety:events:rate_limited": 4,
        }

        def fake_zcount(key: str, start: float, end: float) -> int:
            return counts_by_key[key]

        mock_redis.zcount = Mock(side_effect=fake_zcount)

        total = monitor.get_total_event_count(window_hours=1)

        assert total == sum(counts_by_key.values())

    def test_get_total_event_count_partial_redis_failure(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """Test that one event type failing doesn't prevent totaling the rest."""

        def fake_zcount(key: str, start: float, end: float) -> int:
            if key == "safety:events:pii_detected":
                raise Exception("Redis down for this key")
            return 2

        mock_redis.zcount = Mock(side_effect=fake_zcount)

        total = monitor.get_total_event_count(window_hours=1)

        # 4 remaining event types succeed with count=2 each; failing one contributes 0
        assert total == 2 * (len(SafetyMonitor.VALID_EVENT_TYPES) - 1)
