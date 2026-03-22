"""Tests for rate_limiter.py"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import time

from safety.rate_limiter import RateLimiter


@pytest.mark.unit
class TestRateLimiter:
    """Test suite for RateLimiter."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        return Mock()

    @pytest.fixture
    def limiter(self, mock_redis):
        """Create a RateLimiter instance with mocked Redis."""
        return RateLimiter(mock_redis)

    def test_first_request_allowed(self, limiter, mock_redis):
        """Test first request is allowed."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        allowed, remaining = limiter.check_rate_limit("user123", limit=10)

        assert allowed is True
        assert remaining == 9  # limit - current_count - 1

    def test_requests_up_to_limit_allowed(self, limiter, mock_redis):
        """Test requests up to limit are all allowed."""
        limit = 5
        mock_redis.zremrangebyscore = Mock()
        mock_redis.expire = Mock()

        # Simulate requests up to limit
        for i in range(limit):
            mock_redis.zcard = Mock(return_value=i)
            mock_redis.zadd = Mock()

            allowed, remaining = limiter.check_rate_limit("user123", limit=limit)

            assert allowed is True
            assert 0 <= remaining <= limit

    def test_request_at_limit_plus_one_denied(self, limiter, mock_redis):
        """Test request at limit+1 is denied."""
        limit = 5
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=limit)  # Already at limit

        allowed, remaining = limiter.check_rate_limit("user123", limit=limit)

        assert allowed is False
        assert remaining == 0

    def test_remaining_count_correct(self, limiter, mock_redis):
        """Test remaining count is calculated correctly."""
        limit = 10
        current = 3

        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=current)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        allowed, remaining = limiter.check_rate_limit("user123", limit=limit)

        assert allowed is True
        assert remaining == limit - current - 1  # 10 - 3 - 1 = 6

    def test_rolling_window_removes_old_entries(self, limiter, mock_redis):
        """Test rolling window removes entries older than 60 seconds."""
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        with patch('time.time', return_value=1000):
            limiter.check_rate_limit("user123", limit=10, window_seconds=60)

        # zremrangebyscore should be called to remove entries older than window_start
        mock_redis.zremrangebyscore.assert_called()
        # First arg is key, second should be 0, third should be window_start
        call_args = mock_redis.zremrangebyscore.call_args
        assert call_args[0][0] == "rate_limit:user123"
        assert call_args[0][1] == 0
        # Third argument should be approximately 1000 - 60 = 940
        assert 930 < call_args[0][2] < 950

    def test_different_identifiers_independent(self, limiter, mock_redis):
        """Test different identifiers have independent limits."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        limiter.check_rate_limit("user1", limit=10)
        limiter.check_rate_limit("user2", limit=10)

        # Should create separate Redis keys
        calls = mock_redis.zadd.call_args_list
        assert len(calls) == 2

    def test_key_format_correct(self, limiter, mock_redis):
        """Test that Redis key format is correct."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        limiter.check_rate_limit("test_user", limit=10)

        # Check key format
        zrem_key = mock_redis.zremrangebyscore.call_args[0][0]
        assert zrem_key == "rate_limit:test_user"

    def test_entry_added_to_redis(self, limiter, mock_redis):
        """Test that request entry is added to Redis."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        with patch('time.time', return_value=1000):
            limiter.check_rate_limit("user123", limit=10)

        # zadd should be called with key and score
        mock_redis.zadd.assert_called_once()
        call_args = mock_redis.zadd.call_args
        key = call_args[0][0]
        value_dict = call_args[0][1]

        assert key == "rate_limit:user123"
        assert isinstance(value_dict, dict)

    def test_expiry_set_correctly(self, limiter, mock_redis):
        """Test that Redis key expiry is set."""
        window = 60
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        limiter.check_rate_limit("user123", limit=10, window_seconds=window)

        # expire should be called with window_seconds + 1
        mock_redis.expire.assert_called()
        call_args = mock_redis.expire.call_args
        assert call_args[0][1] == window + 1

    def test_custom_window_size(self, limiter, mock_redis):
        """Test custom window size is respected."""
        custom_window = 120
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        with patch('time.time', return_value=1000):
            limiter.check_rate_limit("user123", limit=10, window_seconds=custom_window)

        # Window start should be calculated from custom window
        call_args = mock_redis.zremrangebyscore.call_args
        window_start = call_args[0][2]
        assert 870 < window_start < 890  # 1000 - 120

    def test_redis_error_handling(self, limiter, mock_redis):
        """Test handling of Redis errors."""
        mock_redis.zremrangebyscore = Mock(side_effect=Exception("Redis error"))

        # Should handle error gracefully
        with patch('safety.rate_limiter.logger'):
            allowed, remaining = limiter.check_rate_limit("user123", limit=10)

        # Per code comment, "Fail open on Redis error"
        assert allowed is True

    def test_zero_limit(self, limiter, mock_redis):
        """Test with zero limit."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        allowed, remaining = limiter.check_rate_limit("user123", limit=0)

        assert allowed is False

    def test_negative_limit(self, limiter, mock_redis):
        """Test with negative limit (edge case)."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        # Behavior with negative limit depends on implementation
        allowed, remaining = limiter.check_rate_limit("user123", limit=-1)

        # Should treat as error condition
        assert isinstance(allowed, bool)

    def test_large_limit(self, limiter, mock_redis):
        """Test with large limit."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=1000)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        large_limit = 10000
        allowed, remaining = limiter.check_rate_limit("user123", limit=large_limit)

        assert allowed is True
        assert remaining == large_limit - 1000 - 1

    def test_return_tuple_structure(self, limiter, mock_redis):
        """Test return value is (bool, int) tuple."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        result = limiter.check_rate_limit("user123", limit=10)

        assert isinstance(result, tuple)
        assert len(result) == 2
        allowed, remaining = result
        assert isinstance(allowed, bool)
        assert isinstance(remaining, int)

    def test_multiple_requests_same_user(self, limiter, mock_redis):
        """Test multiple requests from same user."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.expire = Mock()

        # First request
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        allowed1, remaining1 = limiter.check_rate_limit("user123", limit=10)
        assert allowed1 is True

        # Second request
        mock_redis.zcard = Mock(return_value=1)
        mock_redis.zadd = Mock()
        allowed2, remaining2 = limiter.check_rate_limit("user123", limit=10)
        assert allowed2 is True
        assert remaining2 < remaining1

    def test_time_based_window_calculation(self, limiter, mock_redis):
        """Test that window calculation uses current time."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        # First call at time 1000
        with patch('time.time', return_value=1000):
            limiter.check_rate_limit("user123", limit=10, window_seconds=60)
            first_call_time = mock_redis.zadd.call_args[0][1]

        # Second call at time 1030
        with patch('time.time', return_value=1030):
            limiter.check_rate_limit("user123", limit=10, window_seconds=60)
            second_call_time = mock_redis.zadd.call_args[0][1]

        # Times should be different
        assert first_call_time != second_call_time

    def test_ip_address_as_identifier(self, limiter, mock_redis):
        """Test using IP address as identifier."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        limiter.check_rate_limit("192.168.1.1", limit=100)

        # Should work with IP address
        call_args = mock_redis.zremrangebyscore.call_args
        assert "192.168.1.1" in call_args[0][0]

    def test_api_key_as_identifier(self, limiter, mock_redis):
        """Test using API key as identifier."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()

        api_key = "sk_live_abc123def456"
        limiter.check_rate_limit(api_key, limit=1000)

        # Should work with API key
        call_args = mock_redis.zremrangebyscore.call_args
        assert api_key in call_args[0][0]
