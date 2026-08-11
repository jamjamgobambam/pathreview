"""Tests for monitoring.py"""

from unittest.mock import Mock, patch

import pytest

from safety.monitoring import SafetyMonitor


@pytest.mark.unit
class TestSafetyMonitor:
    """Test suite for SafetyMonitor."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        return Mock()

    @pytest.fixture
    def monitor(self, mock_redis):
        """Create a SafetyMonitor instance with mocked Redis."""
        return SafetyMonitor(mock_redis)

    def test_log_event_valid_type_calls_zadd(self, monitor, mock_redis):
        """Test log_event with a valid event_type calls zadd with the correct key
        and sets a 24h expiry."""
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        monitor.log_event("pii_detected", {"source": "prompt"})

        # zadd should be called with the correctly formatted key
        mock_redis.zadd.assert_called_once()
        call_args = mock_redis.zadd.call_args
        key = call_args[0][0]
        value_dict = call_args[0][1]

        assert key == "safety:events:z:pii_detected"
        assert isinstance(value_dict, dict)

        # expire should be set to 86400 (24 hours)
        mock_redis.expire.assert_called_once()
        expire_args = mock_redis.expire.call_args
        assert expire_args[0][0] == "safety:events:z:pii_detected"
        assert expire_args[0][1] == 86400

    def test_log_event_invalid_type_does_not_call_zadd(self, monitor, mock_redis):
        """Test log_event with an invalid event_type does NOT call zadd, just logs a warning."""
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        with patch("safety.monitoring.logger") as mock_logger:
            monitor.log_event("not_a_real_event", {"source": "prompt"})

        # No Redis write should happen for an unknown event type
        mock_redis.zadd.assert_not_called()
        mock_redis.expire.assert_not_called()

        # A warning should be logged
        mock_logger.warning.assert_called_once()
        warn_args = mock_logger.warning.call_args
        assert warn_args[0][0] == "unknown_event_type"

    def test_log_event_same_timestamp_does_not_overwrite(self, monitor, mock_redis):
        """Test two events logged at the same timestamp use distinct sorted-set members.

        This pins down the fix for the sorted-set member collision issue found in PR
        review: Redis sorted-set members must be unique, so using the bare timestamp
        as the member meant two events sharing a time.time() value would overwrite
        each other and undercount. The member now carries a UUID suffix, so identical
        timestamps still produce two separate entries.
        """
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        # Both calls see the exact same clock reading.
        with patch("time.time", return_value=10000.0):
            monitor.log_event("pii_detected", {"source": "prompt"})
            monitor.log_event("pii_detected", {"source": "prompt"})

        assert mock_redis.zadd.call_count == 2

        members = []
        for call_args in mock_redis.zadd.call_args_list:
            assert call_args[0][0] == "safety:events:z:pii_detected"
            value_dict = call_args[0][1]
            assert len(value_dict) == 1
            member, score = next(iter(value_dict.items()))
            # The score stays the raw timestamp so window pruning still works.
            assert score == 10000.0
            members.append(member)

        # Same timestamp, but the members must differ or the second event would
        # silently replace the first.
        assert members[0] != members[1]

    def test_get_event_count_returns_zcard_result(self, monitor, mock_redis):
        """Test get_event_count returns the zcard result when the key exists."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=7)

        count = monitor.get_event_count("injection_attempt")

        assert count == 7

    def test_get_event_count_empty_returns_zero(self, monitor, mock_redis):
        """Test get_event_count returns 0 when the sorted set is empty/missing."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        count = monitor.get_event_count("injection_attempt")

        assert count == 0

    def test_get_event_count_prunes_window_before_counting(self, monitor, mock_redis):
        """Test get_event_count calls zremrangebyscore with the correct window_start
        before counting."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        with patch("time.time", return_value=10000):
            monitor.get_event_count("rate_limited", window_hours=2)

        # zremrangebyscore should prune entries older than window_start
        mock_redis.zremrangebyscore.assert_called_once()
        call_args = mock_redis.zremrangebyscore.call_args
        # First arg is key, second should be 0, third should be window_start
        assert call_args[0][0] == "safety:events:z:rate_limited"
        assert call_args[0][1] == 0
        # window_start = 10000 - (2 * 3600) = 2800
        assert call_args[0][2] == 10000 - (2 * 3600)

    def test_get_event_count_redis_error_returns_zero(self, monitor, mock_redis):
        """Test get_event_count returns 0 and logs an error if redis raises an exception."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(side_effect=Exception("Redis error"))

        with patch("safety.monitoring.logger") as mock_logger:
            count = monitor.get_event_count("content_filtered")

        assert count == 0
        mock_logger.error.assert_called_once()
        error_args = mock_logger.error.call_args
        assert error_args[0][0] == "event_count_error"

    def test_get_event_count_only_counts_within_window(self, monitor, mock_redis):
        """Test get_event_count returns the post-prune count, not the raw pre-prune total.

        This pins down the fix for issue #68: get_event_count's return value must
        reflect the number of events remaining after old entries are pruned from the
        sorted set, not the total number of events ever logged. zremrangebyscore is a
        no-op here (its result is irrelevant); what matters is that the returned value
        is exactly what zcard reports once pruning has occurred.
        """
        mock_redis.zremrangebyscore = Mock()
        # After pruning, only 3 entries remain inside the window.
        mock_redis.zcard = Mock(return_value=3)

        count = monitor.get_event_count("pii_detected", window_hours=1)

        # Pruning must run before counting, and the return value must be the
        # post-prune count reported by zcard.
        mock_redis.zremrangebyscore.assert_called_once()
        assert count == 3
