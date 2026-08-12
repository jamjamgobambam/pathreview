"""Tests for safety/monitoring.py

Reproduction for issue #66: "Safety monitoring doesn't emit metrics when the
content filter is bypassed by a multi-turn conversation."

Root cause
----------
`SafetyMonitor.log_event` stores a single cumulative counter per event type
(`INCR safety:events:{type}`) with a key-level 24h expiry. Because individual
events carry no timestamps, `SafetyMonitor.get_event_count(window_hours=...)`
cannot compute a rolling-window count. The `window_hours` argument is accepted
but ignored (its own docstring says "not enforced here"), so any multi-turn /
time-window detection silently returns the all-time total instead of the count
within the requested window.

The `test_window_hours_is_ignored_reproduces_66` test below documents the
CORRECT (post-fix) expectation and therefore FAILS against the current
implementation — that failure is the reproduction of the bug.
"""

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

    def test_log_event_rejects_unknown_type(self, monitor: SafetyMonitor, mock_redis: Mock) -> None:
        """Unknown event types are ignored and never written to Redis."""
        monitor.log_event("not_a_real_event", {"foo": "bar"})
        mock_redis.incr.assert_not_called()
        mock_redis.zadd.assert_not_called()

    def test_log_event_writes_timestamped_entry(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """log_event stores a sorted-set entry scored by timestamp + sets expiry."""
        monitor.log_event("content_filtered", {"reason": "test"})

        mock_redis.zadd.assert_called_once()
        key, mapping = mock_redis.zadd.call_args[0]
        assert key == "safety:events:content_filtered"
        # Single member whose value equals its score (the timestamp).
        ((member, score),) = mapping.items()
        assert float(member) == score
        mock_redis.expire.assert_called_once_with("safety:events:content_filtered", 86400)

    def test_get_event_count_trims_then_counts_window(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """get_event_count trims by window_start and returns the sorted-set size."""
        mock_redis.zcard = Mock(return_value=3)

        count = monitor.get_event_count("content_filtered", window_hours=2)

        mock_redis.zremrangebyscore.assert_called_once()
        key, low, high = mock_redis.zremrangebyscore.call_args[0]
        assert key == "safety:events:content_filtered"
        assert low == 0
        assert high > 0  # window_start = now - 2h, a timestamp in the past
        assert count == 3

    def test_get_event_count_returns_zero_on_error(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """A Redis failure is swallowed and yields 0 (fail-closed count)."""
        mock_redis.zremrangebyscore = Mock(side_effect=Exception("redis down"))
        assert monitor.get_event_count("content_filtered") == 0

    def test_window_hours_is_ignored_reproduces_66(
        self, monitor: SafetyMonitor, mock_redis: Mock
    ) -> None:
        """REPRODUCTION (#66): get_event_count ignores window_hours.

        Scenario: over the lifetime of the key, 5 ``content_filtered`` events
        have been recorded, but only 2 of them occurred within the last hour
        (a multi-turn conversation slowly tripping the filter).

        A correct, window-aware implementation must return **2** for
        ``window_hours=1``. The current implementation stores only a lifetime
        counter, so it returns **5** — proving the window is not enforced.

        We mock both access patterns so this test is agnostic to the fix:
          - ``get``  -> current (buggy) lifetime-counter model returns 5
          - ``zcard`` -> a sorted-set, window-aware model returns 2
        """
        # Lifetime total the current implementation reads via GET.
        mock_redis.get = Mock(return_value=b"5")
        # Count within the 1-hour window a windowed implementation would read.
        mock_redis.zcard = Mock(return_value=2)

        count = monitor.get_event_count("content_filtered", window_hours=1)

        assert count == 2, (
            f"window_hours ignored: got {count} (all-time total) instead of 2 "
            "(events within the last hour). A multi-turn bypass that trips the "
            "filter across turns is not reflected in a windowed metric."
        )
