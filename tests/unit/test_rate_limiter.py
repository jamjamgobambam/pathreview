"""Tests for rate_limiter.py"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from safety.rate_limiter import RateLimiter

TEST_IP = "127.0.0.1"


@pytest.mark.unit
class TestRateLimiter:
    """Test suite for RateLimiter."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client with a working pipeline."""
        client = Mock()
        pipe = MagicMock()
        client.pipeline.return_value = pipe
        return client

    @pytest.fixture
    def limiter(self, mock_redis):
        """Create a RateLimiter instance with mocked Redis."""
        return RateLimiter(mock_redis)

    def test_first_request_allowed(self, limiter, mock_redis):
        """Test first request is allowed."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        allowed, remaining = limiter.check_rate_limit("user123", limit=10, ip_address=TEST_IP)

        assert allowed is True
        assert remaining == 9  # limit - current_count - 1

    def test_requests_up_to_limit_allowed(self, limiter, mock_redis):
        """Test requests up to limit are all allowed."""
        limit = 5
        mock_redis.zremrangebyscore = Mock()

        # Simulate requests up to limit (same count for IP and user buckets)
        for i in range(limit):
            mock_redis.zcard = Mock(return_value=i)

            allowed, remaining = limiter.check_rate_limit(
                "user123", limit=limit, ip_address=TEST_IP
            )

            assert allowed is True
            assert 0 <= remaining <= limit

    def test_request_at_limit_plus_one_denied(self, limiter, mock_redis):
        """Test request at limit+1 is denied."""
        limit = 5
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=limit)  # Already at limit

        allowed, remaining = limiter.check_rate_limit("user123", limit=limit, ip_address=TEST_IP)

        assert allowed is False
        assert remaining == 0

    def test_remaining_count_correct(self, limiter, mock_redis):
        """Test remaining count is calculated correctly."""
        limit = 10
        current = 3

        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=current)

        allowed, remaining = limiter.check_rate_limit("user123", limit=limit, ip_address=TEST_IP)

        assert allowed is True
        assert remaining == limit - current - 1  # 10 - 3 - 1 = 6

    def test_rolling_window_removes_old_entries(self, limiter, mock_redis):
        """Test rolling window removes entries older than 60 seconds."""
        mock_redis.zcard = Mock(return_value=0)

        with patch("time.time", return_value=1000):
            limiter.check_rate_limit("user123", limit=10, window_seconds=60, ip_address=TEST_IP)

        # zremrangebyscore should be called for IP and user keys
        mock_redis.zremrangebyscore.assert_called()
        call_args = mock_redis.zremrangebyscore.call_args_list[0]
        assert call_args[0][0] == f"rate_limit:ip:{TEST_IP}"
        assert call_args[0][1] == 0
        # Third argument should be approximately 1000 - 60 = 940
        assert 930 < call_args[0][2] < 950

    def test_different_identifiers_independent(self, limiter, mock_redis):
        """Test different identifiers have independent limits."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        limiter.check_rate_limit("user1", limit=10, ip_address=TEST_IP)
        limiter.check_rate_limit("user2", limit=10, ip_address="10.0.0.2")

        # Each allowed request records IP + user via pipeline zadd
        pipe = mock_redis.pipeline.return_value
        assert pipe.zadd.call_count == 4

    def test_key_format_correct(self, limiter, mock_redis):
        """Test that Redis key format is correct for IP and user."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        limiter.check_rate_limit("test_user", limit=10, ip_address=TEST_IP)

        keys = [call[0][0] for call in mock_redis.zremrangebyscore.call_args_list]
        assert f"rate_limit:ip:{TEST_IP}" in keys
        assert "rate_limit:user:test_user" in keys

    def test_entry_added_to_redis(self, limiter, mock_redis):
        """Test that request entries are added to Redis for IP and user."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        pipe = mock_redis.pipeline.return_value

        with patch("time.time", return_value=1000):
            limiter.check_rate_limit("user123", limit=10, ip_address=TEST_IP)

        assert pipe.zadd.call_count == 2
        zadd_keys = [call[0][0] for call in pipe.zadd.call_args_list]
        assert f"rate_limit:ip:{TEST_IP}" in zadd_keys
        assert "rate_limit:user:user123" in zadd_keys
        for call in pipe.zadd.call_args_list:
            members = call[0][1]
            assert isinstance(members, dict)
            member = next(iter(members))
            assert member.startswith("1000:")
            assert members[member] == 1000
        pipe.execute.assert_called_once()

    def test_expiry_set_correctly(self, limiter, mock_redis):
        """Test that Redis key expiry is set."""
        window = 60
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        pipe = mock_redis.pipeline.return_value

        limiter.check_rate_limit("user123", limit=10, window_seconds=window, ip_address=TEST_IP)

        assert pipe.expire.call_count == 2
        for call in pipe.expire.call_args_list:
            assert call[0][1] == window + 1

    def test_custom_window_size(self, limiter, mock_redis):
        """Test custom window size is respected."""
        custom_window = 120
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        with patch("time.time", return_value=1000):
            limiter.check_rate_limit(
                "user123",
                limit=10,
                window_seconds=custom_window,
                ip_address=TEST_IP,
            )

        # Window start should be calculated from custom window
        call_args = mock_redis.zremrangebyscore.call_args_list[0]
        window_start = call_args[0][2]
        assert 870 < window_start < 890  # 1000 - 120

    def test_redis_error_handling(self, limiter, mock_redis):
        """Test handling of Redis errors."""
        mock_redis.zremrangebyscore = Mock(side_effect=Exception("Redis error"))

        # Should handle error gracefully
        with patch("safety.rate_limiter.logger"):
            allowed, remaining = limiter.check_rate_limit("user123", limit=10, ip_address=TEST_IP)

        # Per code comment, "Fail open on Redis error"
        assert allowed is True
        assert remaining == 10

    def test_zero_limit(self, limiter, mock_redis):
        """Test with zero limit."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        allowed, remaining = limiter.check_rate_limit("user123", limit=0, ip_address=TEST_IP)

        assert allowed is False

    def test_negative_limit(self, limiter, mock_redis):
        """Test with negative limit (edge case)."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        # Behavior with negative limit depends on implementation
        allowed, remaining = limiter.check_rate_limit("user123", limit=-1, ip_address=TEST_IP)

        # Should treat as error condition
        assert isinstance(allowed, bool)

    def test_large_limit(self, limiter, mock_redis):
        """Test with large limit."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=1000)

        large_limit = 10000
        allowed, remaining = limiter.check_rate_limit(
            "user123", limit=large_limit, ip_address=TEST_IP
        )

        assert allowed is True
        assert remaining == large_limit - 1000 - 1

    def test_return_tuple_structure(self, limiter, mock_redis):
        """Test return value is (bool, int) tuple."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        result = limiter.check_rate_limit("user123", limit=10, ip_address=TEST_IP)

        assert isinstance(result, tuple)
        assert len(result) == 2
        allowed, remaining = result
        assert isinstance(allowed, bool)
        assert isinstance(remaining, int)

    def test_multiple_requests_same_user(self, limiter, mock_redis):
        """Test multiple requests from same user."""
        mock_redis.zremrangebyscore = Mock()

        # First request
        mock_redis.zcard = Mock(return_value=0)
        allowed1, remaining1 = limiter.check_rate_limit("user123", limit=10, ip_address=TEST_IP)
        assert allowed1 is True

        # Second request
        mock_redis.zcard = Mock(return_value=1)
        allowed2, remaining2 = limiter.check_rate_limit("user123", limit=10, ip_address=TEST_IP)
        assert allowed2 is True
        assert remaining2 < remaining1

    def test_time_based_window_calculation(self, limiter, mock_redis):
        """Test that window calculation uses current time."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        pipe = mock_redis.pipeline.return_value

        # First call at time 1000
        with patch("time.time", return_value=1000):
            limiter.check_rate_limit("user123", limit=10, window_seconds=60, ip_address=TEST_IP)
            first_members = pipe.zadd.call_args_list[0][0][1]

        pipe.zadd.reset_mock()

        # Second call at time 1030
        with patch("time.time", return_value=1030):
            limiter.check_rate_limit("user123", limit=10, window_seconds=60, ip_address=TEST_IP)
            second_members = pipe.zadd.call_args_list[0][0][1]

        # Scores (and members) should differ across timestamps
        assert first_members != second_members
        assert next(iter(first_members.values())) == 1000
        assert next(iter(second_members.values())) == 1030

    def test_ip_address_as_identifier(self, limiter, mock_redis):
        """Test IP is tracked via the dedicated ip_address parameter."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        limiter.check_rate_limit(None, limit=100, ip_address="192.168.1.1")

        call_args = mock_redis.zremrangebyscore.call_args
        assert call_args[0][0] == "rate_limit:ip:192.168.1.1"

    def test_api_key_as_identifier(self, limiter, mock_redis):
        """Test using API key as identifier."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        api_key = "sk_live_abc123def456"
        limiter.check_rate_limit(api_key, limit=1000, ip_address=TEST_IP)

        keys = [call[0][0] for call in mock_redis.zremrangebyscore.call_args_list]
        assert f"rate_limit:user:{api_key}" in keys

    def test_reproduce_ip_rate_limit_gap(self, limiter, mock_redis):
        """Same IP with different user IDs is denied once the IP bucket is full.

        Previously only the user identifier was checked, so rotating user IDs
        bypassed the limit. After the fix, the shared IP bucket blocks further
        requests.
        """
        limit = 5
        mock_redis.zremrangebyscore = Mock()

        # First `limit` requests: IP count rises 0..limit-1; each has a fresh user
        for i in range(limit):
            mock_redis.zcard = Mock(side_effect=[i, 0])  # IP count, user count
            allowed, _ = limiter.check_rate_limit(f"user{i}", limit=limit, ip_address=TEST_IP)
            assert allowed is True

        # Next request from a new user on the same IP must be denied
        mock_redis.zcard = Mock(return_value=limit)
        allowed, remaining = limiter.check_rate_limit("user_new", limit=limit, ip_address=TEST_IP)
        assert allowed is False
        assert remaining == 0

    def test_ip_over_limit_denies_even_when_user_under(self, limiter, mock_redis):
        """IP at limit denies even if the user bucket is empty."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=5)

        allowed, remaining = limiter.check_rate_limit("user123", limit=5, ip_address=TEST_IP)

        assert allowed is False
        assert remaining == 0
        mock_redis.pipeline.return_value.execute.assert_not_called()

    def test_user_over_limit_denies_even_when_ip_under(self, limiter, mock_redis):
        """User at limit denies even if the IP bucket has room."""
        mock_redis.zremrangebyscore = Mock()
        # IP under limit (2), user at limit (5)
        mock_redis.zcard = Mock(side_effect=[2, 5])

        allowed, remaining = limiter.check_rate_limit("user123", limit=5, ip_address=TEST_IP)

        assert allowed is False
        assert remaining == 0
        mock_redis.pipeline.return_value.execute.assert_not_called()

    def test_unauthenticated_tracks_ip_only(self, limiter, mock_redis):
        """Unauthenticated requests only record the IP key."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        pipe = mock_redis.pipeline.return_value

        allowed, remaining = limiter.check_rate_limit(None, limit=10, ip_address=TEST_IP)

        assert allowed is True
        assert remaining == 9
        assert mock_redis.zremrangebyscore.call_count == 1
        assert mock_redis.zremrangebyscore.call_args[0][0] == f"rate_limit:ip:{TEST_IP}"
        assert pipe.zadd.call_count == 1
        assert pipe.zadd.call_args[0][0] == f"rate_limit:ip:{TEST_IP}"

    def test_remaining_is_min_of_ip_and_user(self, limiter, mock_redis):
        """Remaining reflects the tighter of the two buckets."""
        mock_redis.zremrangebyscore = Mock()
        # IP has 8 used (1 left after this), user has 2 used (7 left after this)
        mock_redis.zcard = Mock(side_effect=[8, 2])

        allowed, remaining = limiter.check_rate_limit("user123", limit=10, ip_address=TEST_IP)

        assert allowed is True
        assert remaining == 1  # min(10-8-1, 10-2-1) = min(1, 7)

    def test_ip_and_user_keys_do_not_collide(self, limiter, mock_redis):
        """Identifier equal to the IP still uses distinct Redis key prefixes."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)

        limiter.check_rate_limit(TEST_IP, limit=10, ip_address=TEST_IP)

        keys = [call[0][0] for call in mock_redis.zremrangebyscore.call_args_list]
        assert keys == [f"rate_limit:ip:{TEST_IP}", f"rate_limit:user:{TEST_IP}"]

    def test_zadd_members_unique_at_same_timestamp(self, limiter, mock_redis):
        """Concurrent requests at the same timestamp get distinct ZADD members."""
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=0)
        pipe = mock_redis.pipeline.return_value

        with patch("time.time", return_value=1000.0):
            limiter.check_rate_limit("user123", limit=10, ip_address=TEST_IP)
            first_member = next(iter(pipe.zadd.call_args_list[0][0][1]))

        pipe.zadd.reset_mock()

        with patch("time.time", return_value=1000.0):
            limiter.check_rate_limit("user123", limit=10, ip_address=TEST_IP)
            second_member = next(iter(pipe.zadd.call_args_list[0][0][1]))

        assert first_member != second_member
        assert first_member.startswith("1000.0:")
        assert second_member.startswith("1000.0:")
