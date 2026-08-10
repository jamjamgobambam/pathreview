"""Tests for safety event monitoring."""

from unittest.mock import Mock, patch

import pytest

from safety.monitoring import SafetyMonitor


@pytest.mark.unit
class TestSafetyMonitor:
    """Test suite for SafetyMonitor."""

    def test_log_event_records_recent_event(self):
        """Valid safety events should be stored for rolling-window counting."""
        mock_redis = Mock()
        monitor = SafetyMonitor(mock_redis)

        with patch("safety.monitoring.time.time", return_value=100000):
            monitor.log_event(
                "pii_detected",
                {"source": "resume"},
            )

        mock_redis.incr.assert_called_once_with(
            "safety:events:pii_detected"
        )

        mock_redis.zadd.assert_called_once()

        key = mock_redis.zadd.call_args[0][0]
        event_data = mock_redis.zadd.call_args[0][1]

        assert key == "safety:events:recent"
        assert len(event_data) == 1
        assert list(event_data.values())[0] == 100000

    def test_get_recent_event_count(self):
        """Count only safety events inside the requested time window."""
        mock_redis = Mock()
        mock_redis.zcount.return_value = 3

        monitor = SafetyMonitor(mock_redis)

        with patch("safety.monitoring.time.time", return_value=100000):
            count = monitor.get_recent_event_count(window_hours=1)

        assert count == 3

        mock_redis.zcount.assert_called_once_with(
            "safety:events:recent",
            96400,
            100000,
        )

    def test_get_recent_event_count_returns_zero_on_error(self):
        """Redis errors should return zero instead of breaking monitoring."""
        mock_redis = Mock()
        mock_redis.zcount.side_effect = Exception("Redis unavailable")

        monitor = SafetyMonitor(mock_redis)

        count = monitor.get_recent_event_count(window_hours=1)

        assert count == 0