import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from safety.monitoring import SafetyMonitor


FROZEN_NOW = datetime(2026, 8, 4, 10, 30, 0)


class _FrozenDateTime(datetime):
    """datetime subclass whose utcnow() always returns a fixed instant."""

    @classmethod
    def utcnow(cls):
        return FROZEN_NOW


@pytest.mark.unit
class TestSafetyMonitor:
    """Test suite for SafetyMonitor."""

    @pytest.fixture(autouse=True)
    def freeze_time(self, monkeypatch):
        """Freeze safety.monitoring.datetime.utcnow() for every test."""
        monkeypatch.setattr("safety.monitoring.datetime", _FrozenDateTime)

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client backed by an in-memory dict store."""
        store = {}

        def incr(key):
            store[key] = store.get(key, 0) + 1
            return store[key]

        def get(key):
            value = store.get(key)
            return str(value) if value is not None else None

        def expire(key, seconds):
            return True

        client = Mock()
        client.incr = Mock(side_effect=incr)
        client.get = Mock(side_effect=get)
        client.expire = Mock(side_effect=expire)
        client.store = store
        return client

    @pytest.fixture
    def monitor(self, mock_redis_client):
        """Create a SafetyMonitor instance."""
        return SafetyMonitor(mock_redis_client)

    def test_valid_event_increments_current_hour_bucket(self, monitor, mock_redis_client):
        """Test that logging a valid event increments the current hour's bucket."""
        monitor.log_event("pii_detected", {"user": "alice"})

        expected_key = "safety:events:pii_detected:2026080410"
        assert mock_redis_client.store[expected_key] == 1
        mock_redis_client.incr.assert_called_once_with(expected_key)

    def test_multiple_events_same_type_same_hour_accumulate(self, monitor, mock_redis_client):
        """Test that repeated events of the same type in the same hour accumulate."""
        monitor.log_event("pii_detected", {"user": "alice"})
        monitor.log_event("pii_detected", {"user": "bob"})

        expected_key = "safety:events:pii_detected:2026080410"
        assert mock_redis_client.store[expected_key] == 2

    def test_sets_expiry_on_the_bucket_key(self, monitor, mock_redis_client):
        """Test that the hourly bucket key is given a 48 hour expiry."""
        monitor.log_event("rate_limited", {})

        expected_key = "safety:events:rate_limited:2026080410"
        mock_redis_client.expire.assert_called_once_with(expected_key, 172800)

    def test_unknown_event_type_is_ignored(self, monitor, mock_redis_client):
        """Test that an unrecognized event type is not written to Redis."""
        monitor.log_event("not_a_real_event_type", {"foo": "bar"})

        mock_redis_client.incr.assert_not_called()
        mock_redis_client.expire.assert_not_called()
        assert mock_redis_client.store == {}

    def test_different_event_types_get_separate_keys(self, monitor, mock_redis_client):
        """Test that different event types are tracked under separate keys."""
        monitor.log_event("pii_detected", {})
        monitor.log_event("injection_attempt", {})

        assert mock_redis_client.store["safety:events:pii_detected:2026080410"] == 1
        assert mock_redis_client.store["safety:events:injection_attempt:2026080410"] == 1

    def test_redis_failure_on_log_is_caught_and_does_not_raise(self, monitor, mock_redis_client):
        """Test that a Redis failure during log_event is caught rather than raised."""
        mock_redis_client.incr.side_effect = ConnectionError("redis unreachable")

        monitor.log_event("pii_detected", {"user": "alice"})

    def test_get_event_count_returns_zero_when_no_events_logged(self, monitor):
        """Test that get_event_count returns 0 when nothing has been logged."""
        assert monitor.get_event_count("pii_detected", window_hours=1) == 0

    def test_get_event_count_counts_events_in_current_hour(self, monitor):
        """Test that get_event_count sums events logged in the current hour."""
        monitor.log_event("pii_detected", {})
        monitor.log_event("pii_detected", {})
        monitor.log_event("pii_detected", {})

        assert monitor.get_event_count("pii_detected", window_hours=1) == 3

    def test_get_event_count_window_includes_prior_hours(self, monitor, mock_redis_client):
        """Test that widening the window includes counts from earlier hours."""
        mock_redis_client.store["safety:events:pii_detected:2026080409"] = 5
        monitor.log_event("pii_detected", {})

        assert monitor.get_event_count("pii_detected", window_hours=1) == 1
        assert monitor.get_event_count("pii_detected", window_hours=2) == 6

    def test_get_event_count_excludes_hours_outside_window(self, monitor, mock_redis_client):
        """Test that hours outside the requested window are not counted."""
        mock_redis_client.store["safety:events:pii_detected:2026080407"] = 100
        monitor.log_event("pii_detected", {})

        assert monitor.get_event_count("pii_detected", window_hours=2) == 1

    def test_get_event_count_different_event_types_are_independent(self, monitor):
        """Test that counts for one event type do not affect another."""
        monitor.log_event("pii_detected", {})
        monitor.log_event("injection_attempt", {})
        monitor.log_event("injection_attempt", {})

        assert monitor.get_event_count("pii_detected", window_hours=1) == 1
        assert monitor.get_event_count("injection_attempt", window_hours=1) == 2

    def test_get_event_count_redis_failure_returns_zero(self, monitor, mock_redis_client):
        """Test that a Redis failure during get_event_count returns 0, not an exception."""
        mock_redis_client.get.side_effect = ConnectionError("redis unreachable")

        assert monitor.get_event_count("pii_detected", window_hours=1) == 0

    def test_get_total_event_count_returns_zero_when_no_events(self, monitor):
        """Test that get_total_event_count returns 0 when nothing has been logged."""
        assert monitor.get_total_event_count(window_hours=1) == 0

    def test_get_total_event_count_sums_across_all_event_types(self, monitor):
        """Test that get_total_event_count aggregates counts across every event type."""
        monitor.log_event("pii_detected", {})
        monitor.log_event("pii_detected", {})
        monitor.log_event("injection_attempt", {})
        monitor.log_event("content_filtered", {})
        monitor.log_event("bias_detected", {})
        monitor.log_event("rate_limited", {})

        assert monitor.get_total_event_count(window_hours=1) == 6

    def test_get_total_event_count_ignores_unknown_event_types(self, monitor):
        """Test that unknown event types never contribute to the total."""
        monitor.log_event("pii_detected", {})
        monitor.log_event("bogus_type", {})

        assert monitor.get_total_event_count(window_hours=1) == 1

    def test_get_total_event_count_respects_window_hours(self, monitor, mock_redis_client):
        """Test that get_total_event_count only includes hours within the window."""
        mock_redis_client.store["safety:events:pii_detected:2026080405"] = 10
        monitor.log_event("injection_attempt", {})

        assert monitor.get_total_event_count(window_hours=1) == 1
        assert monitor.get_total_event_count(window_hours=6) == 11

    def test_get_total_event_count_one_failing_type_does_not_break_total(self, monitor, mock_redis_client):
        """Test that a Redis failure for one event type doesn't break the aggregate."""
        monitor.log_event("pii_detected", {})
        monitor.log_event("injection_attempt", {})

        original_get = mock_redis_client.get.side_effect

        def flaky_get(key):
            if "injection_attempt" in key:
                raise ConnectionError("boom")
            return original_get(key)

        mock_redis_client.get.side_effect = flaky_get

        assert monitor.get_total_event_count(window_hours=1) == 1
