"""Tests for time-based safety event monitoring."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from safety.monitoring import SafetyMonitor


@pytest.mark.unit
class TestSafetyMonitor:
    """Test suite for SafetyMonitor."""

    @pytest.fixture
    def redis_client(self) -> Mock:
        """Return a mocked Redis client."""
        return Mock()

    @pytest.fixture
    def monitor(self, redis_client: Mock) -> SafetyMonitor:
        """Return a monitor backed by mocked Redis."""
        return SafetyMonitor(redis_client)

    def test_log_event_stores_timestamped_entry(
        self, monitor: SafetyMonitor, redis_client: Mock
    ) -> None:
        """A valid event should be stored in a timestamped sorted set."""
        with (
            patch("safety.monitoring.time.time", return_value=1000.0),
            patch(
                "safety.monitoring.uuid4",
                return_value=SimpleNamespace(hex="event-id"),
            ),
        ):
            monitor.log_event("pii_detected", {"source": "resume"})

        redis_client.zadd.assert_called_once_with(
            "safety:events:timeline:pii_detected",
            {"1000.0:event-id": 1000.0},
        )
        redis_client.expire.assert_called_once_with(
            "safety:events:timeline:pii_detected",
            SafetyMonitor.RETENTION_SECONDS,
        )

    def test_invalid_event_type_is_ignored(
        self, monitor: SafetyMonitor, redis_client: Mock
    ) -> None:
        """Unknown safety event types should not be written."""
        monitor.log_event("not-valid", {"source": "test"})

        redis_client.zadd.assert_not_called()
        redis_client.expire.assert_not_called()

    def test_log_event_handles_redis_failure(
        self, monitor: SafetyMonitor, redis_client: Mock
    ) -> None:
        """A failed Redis write should be logged without escaping."""
        redis_client.zadd.side_effect = RuntimeError("Redis unavailable")

        with patch("safety.monitoring.logger") as logger:
            monitor.log_event("bias_detected", {"source": "review"})

        logger.error.assert_called_once_with(
            "safety_monitor_error",
            error="Redis unavailable",
        )

    def test_no_events_returns_zero(self, monitor: SafetyMonitor, redis_client: Mock) -> None:
        """An empty rolling window should return zero."""
        redis_client.zcount.return_value = 0

        with patch("safety.monitoring.time.time", return_value=7200.0):
            result = monitor.get_event_count("pii_detected")

        assert result == 0

    def test_recent_events_are_counted(self, monitor: SafetyMonitor, redis_client: Mock) -> None:
        """Recent events should be counted inside the one-hour window."""
        redis_client.zcount.return_value = 3

        with patch("safety.monitoring.time.time", return_value=7200.0):
            result = monitor.get_event_count("injection_attempt")

        assert result == 3
        redis_client.zremrangebyscore.assert_called_once_with(
            "safety:events:timeline:injection_attempt",
            "-inf",
            3600.0,
        )
        redis_client.zcount.assert_called_once_with(
            "safety:events:timeline:injection_attempt",
            3600.0,
            "+inf",
        )

    def test_custom_window_uses_requested_cutoff(
        self, monitor: SafetyMonitor, redis_client: Mock
    ) -> None:
        """The window_hours argument should control the rolling cutoff."""
        redis_client.zcount.return_value = 1

        with patch("safety.monitoring.time.time", return_value=10800.0):
            monitor.get_event_count("content_filtered", window_hours=2)

        redis_client.zremrangebyscore.assert_called_once_with(
            "safety:events:timeline:content_filtered",
            "-inf",
            3600.0,
        )

    def test_non_positive_window_returns_zero(
        self, monitor: SafetyMonitor, redis_client: Mock
    ) -> None:
        """A non-positive window should not query Redis."""
        assert monitor.get_event_count("rate_limited", window_hours=0) == 0
        redis_client.zcount.assert_not_called()

    def test_unknown_event_count_returns_zero(
        self, monitor: SafetyMonitor, redis_client: Mock
    ) -> None:
        """Unknown event types should not query Redis."""
        assert monitor.get_event_count("not-valid") == 0
        redis_client.zcount.assert_not_called()

    def test_read_failure_returns_zero(self, monitor: SafetyMonitor, redis_client: Mock) -> None:
        """A failed Redis read should fail safely to zero."""
        redis_client.zremrangebyscore.side_effect = RuntimeError("Redis unavailable")

        with patch("safety.monitoring.logger") as logger:
            result = monitor.get_event_count("rate_limited")

        assert result == 0
        logger.error.assert_called_once_with(
            "event_count_error",
            event_type="rate_limited",
            error="Redis unavailable",
        )

    def test_total_count_aggregates_all_event_types(self, monitor: SafetyMonitor) -> None:
        """The aggregate should include every valid safety event type."""
        monitor.get_event_count = Mock(return_value=2)  # type: ignore[method-assign]

        result = monitor.get_total_event_count(window_hours=1)

        assert result == 2 * len(SafetyMonitor.VALID_EVENT_TYPES)
        assert monitor.get_event_count.call_count == len(SafetyMonitor.VALID_EVENT_TYPES)
        monitor.get_event_count.assert_any_call("pii_detected", 1)
        monitor.get_event_count.assert_any_call("injection_attempt", 1)
