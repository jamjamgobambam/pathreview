"""Tests for safety/monitoring.py"""

# mypy: ignore-errors
# (tests aren't type-checked; see `make typecheck`, which excludes tests/)

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

    # ---- log_event ----

    def test_log_event_valid_type_increments_redis(self, monitor, mock_redis):
        """A valid event type increments and expires its Redis counter."""
        mock_redis.incr = Mock()
        mock_redis.expire = Mock()

        monitor.log_event("pii_detected", {"field": "email"})

        mock_redis.incr.assert_called_once_with("safety:events:pii_detected")
        mock_redis.expire.assert_called_once_with("safety:events:pii_detected", 86400)

    def test_log_event_invalid_type_ignored(self, monitor, mock_redis):
        """Unknown event types are dropped without touching Redis."""
        mock_redis.incr = Mock()

        with patch("safety.monitoring.logger"):
            monitor.log_event("not_a_real_type", {})

        mock_redis.incr.assert_not_called()

    # ---- get_event_count ----

    def test_get_event_count_returns_int(self, monitor, mock_redis):
        """A stored count is parsed to an int."""
        mock_redis.get = Mock(return_value="5")
        assert monitor.get_event_count("pii_detected") == 5

    def test_get_event_count_missing_key_returns_zero(self, monitor, mock_redis):
        """A missing key counts as zero."""
        mock_redis.get = Mock(return_value=None)
        assert monitor.get_event_count("pii_detected") == 0

    def test_get_event_count_redis_error_returns_zero(self, monitor, mock_redis):
        """A Redis error is swallowed and counts as zero."""
        mock_redis.get = Mock(side_effect=Exception("redis down"))
        with patch("safety.monitoring.logger"):
            assert monitor.get_event_count("pii_detected") == 0

    def test_get_event_count_key_format(self, monitor, mock_redis):
        """The Redis key is namespaced per event type."""
        mock_redis.get = Mock(return_value="1")
        monitor.get_event_count("injection_attempt")
        mock_redis.get.assert_called_once_with("safety:events:injection_attempt")

    # ---- get_total_event_count ----

    def test_total_sums_all_event_types(self, monitor, mock_redis):
        """The total is the sum of every per-type counter."""
        counts = {
            "safety:events:pii_detected": "2",
            "safety:events:injection_attempt": "1",
            "safety:events:content_filtered": "3",
        }
        mock_redis.get = Mock(side_effect=lambda key: counts.get(key))

        assert monitor.get_total_event_count() == 6

    def test_total_zero_when_no_events(self, monitor, mock_redis):
        """With nothing recorded the total is zero (not an error)."""
        mock_redis.get = Mock(return_value=None)
        assert monitor.get_total_event_count() == 0

    def test_total_iterates_every_valid_type(self, monitor, mock_redis):
        """The aggregate queries exactly the known event types."""
        mock_redis.get = Mock(return_value=None)

        monitor.get_total_event_count()

        queried = {call.args[0] for call in mock_redis.get.call_args_list}
        expected = {f"safety:events:{t}" for t in SafetyMonitor.VALID_EVENT_TYPES}
        assert queried == expected

    def test_total_survives_single_type_error(self, monitor, mock_redis):
        """One erroring key contributes 0 without zeroing the whole total."""

        def fake_get(key):
            if key == "safety:events:pii_detected":
                raise Exception("corrupt value")
            if key == "safety:events:rate_limited":
                return "4"
            return None

        mock_redis.get = Mock(side_effect=fake_get)
        with patch("safety.monitoring.logger"):
            assert monitor.get_total_event_count() == 4

    def test_total_reflects_logged_events_end_to_end(self):
        """Reproduction -> fix: logged events surface in the aggregate count.

        This is the value the /health endpoint now reports instead of a
        hardcoded 0 (issue #68).
        """

        class FakeRedis:
            def __init__(self):
                self.store = {}

            def incr(self, key):
                self.store[key] = int(self.store.get(key, 0)) + 1
                return self.store[key]

            def expire(self, key, ttl):
                return True

            def get(self, key):
                value = self.store.get(key)
                return None if value is None else str(value)

        monitor = SafetyMonitor(FakeRedis())
        monitor.log_event("pii_detected", {"field": "email"})
        monitor.log_event("injection_attempt", {"prompt": "ignore previous"})
        monitor.log_event("pii_detected", {"field": "phone"})

        assert monitor.get_total_event_count() == 3
