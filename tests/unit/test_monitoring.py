"""Tests for monitoring.py (Issue #68: safety_events_last_hour)"""

from unittest.mock import MagicMock, patch

import pytest
import redis

from safety.monitoring import (
    DEFAULT_WINDOW_SECONDS,
    EVENT_RETENTION_SECONDS,
    RECENT_EVENTS_KEY_PREFIX,
    SafetyMonitor,
    get_safety_events_last_hour,
)

# Fixed clock so window_start is exactly predictable
FROZEN_NOW = 1_700_000_000.0


@pytest.mark.unit
class TestGetEventsInWindow:
    """Test suite for SafetyMonitor.get_events_in_window."""

    @pytest.fixture
    def mock_pipeline(self) -> MagicMock:
        """Create a mock Redis pipeline that records zcount calls."""
        pipe = MagicMock()
        # One result per event type, summing to 6
        pipe.execute = MagicMock(return_value=[1, 1, 1, 1, 2])
        return pipe

    @pytest.fixture
    def mock_redis(self, mock_pipeline: MagicMock) -> MagicMock:
        """Create a mock Redis client that hands out the mock pipeline."""
        client = MagicMock(spec=redis.Redis)
        client.pipeline = MagicMock(return_value=mock_pipeline)
        return client

    @pytest.fixture
    def monitor(self, mock_redis: MagicMock) -> SafetyMonitor:
        """Create a SafetyMonitor instance with mocked Redis."""
        return SafetyMonitor(mock_redis)

    def test_initializes_redis_pipeline(
        self, monitor: SafetyMonitor, mock_redis: MagicMock, mock_pipeline: MagicMock
    ) -> None:
        """Test a pipeline is opened and executed once (single round trip)."""
        monitor.get_events_in_window(window_seconds=3600)

        mock_redis.pipeline.assert_called_once_with()
        mock_pipeline.execute.assert_called_once_with()

    def test_zcount_called_once_per_valid_event_type(
        self, monitor: SafetyMonitor, mock_pipeline: MagicMock
    ) -> None:
        """Test the method loops over every entry in VALID_EVENT_TYPES."""
        monitor.get_events_in_window(window_seconds=3600)

        assert mock_pipeline.zcount.call_count == len(SafetyMonitor.VALID_EVENT_TYPES)

        queried_keys = {call[0][0] for call in mock_pipeline.zcount.call_args_list}
        expected_keys = {
            f"{RECENT_EVENTS_KEY_PREFIX}:{event_type}"
            for event_type in SafetyMonitor.VALID_EVENT_TYPES
        }
        assert queried_keys == expected_keys

    def test_zcount_uses_recent_events_key_prefix(
        self, monitor: SafetyMonitor, mock_pipeline: MagicMock
    ) -> None:
        """Test every queried key carries the rolling-window key prefix."""
        monitor.get_events_in_window(window_seconds=3600)

        for call in mock_pipeline.zcount.call_args_list:
            key = call[0][0]
            assert key.startswith(f"{RECENT_EVENTS_KEY_PREFIX}:")
            # The suffix must be a real event type, not a stringified set/None
            assert key.rsplit(":", 1)[1] in SafetyMonitor.VALID_EVENT_TYPES

    def test_zcount_window_start_calculated_from_window_seconds(
        self, monitor: SafetyMonitor, mock_pipeline: MagicMock
    ) -> None:
        """Test window_start is now - window_seconds, with +inf upper bound."""
        window_seconds = 900

        with patch("safety.monitoring.time.time", return_value=FROZEN_NOW):
            monitor.get_events_in_window(window_seconds=window_seconds)

        expected_min = f"({FROZEN_NOW - window_seconds}"  # "(1699999100.0"
        for call in mock_pipeline.zcount.call_args_list:
            _key, min_score, max_score = call[0]
            assert min_score == expected_min
            assert max_score == "+inf"

    def test_window_start_lower_bound_is_exclusive(
        self, monitor: SafetyMonitor, mock_pipeline: MagicMock
    ) -> None:
        """Test the lower bound is exclusive so counts are strictly in-window."""
        with patch("safety.monitoring.time.time", return_value=FROZEN_NOW):
            monitor.get_events_in_window(window_seconds=3600)

        for call in mock_pipeline.zcount.call_args_list:
            min_score = call[0][1]
            # Redis treats a leading "(" as an exclusive range bound
            assert min_score.startswith("(")
            assert float(min_score[1:]) == FROZEN_NOW - 3600

    def test_returns_summed_integer_from_pipeline_execute(
        self, monitor: SafetyMonitor, mock_pipeline: MagicMock
    ) -> None:
        """Test the return value is the sum of the pipeline results."""
        mock_pipeline.execute = MagicMock(return_value=[3, 0, 7, 1, 4])

        result = monitor.get_events_in_window(window_seconds=3600)

        assert result == 15
        assert isinstance(result, int)

    def test_returns_zero_when_no_events_in_window(
        self, monitor: SafetyMonitor, mock_pipeline: MagicMock
    ) -> None:
        """Test an empty window counts as zero, not None."""
        mock_pipeline.execute = MagicMock(return_value=[0] * len(SafetyMonitor.VALID_EVENT_TYPES))

        assert monitor.get_events_in_window(window_seconds=3600) == 0

    def test_default_window_is_one_hour(
        self, monitor: SafetyMonitor, mock_pipeline: MagicMock
    ) -> None:
        """Test the default window is 3600 seconds."""
        assert DEFAULT_WINDOW_SECONDS == 3600

        with patch("safety.monitoring.time.time", return_value=FROZEN_NOW):
            monitor.get_events_in_window()

        min_score = mock_pipeline.zcount.call_args_list[0][0][1]
        assert float(min_score[1:]) == FROZEN_NOW - 3600

    def test_larger_window_reaches_further_back(
        self, monitor: SafetyMonitor, mock_pipeline: MagicMock
    ) -> None:
        """Test a wider window produces an earlier window_start."""
        with patch("safety.monitoring.time.time", return_value=FROZEN_NOW):
            monitor.get_events_in_window(window_seconds=60)
            narrow = float(mock_pipeline.zcount.call_args_list[0][0][1][1:])

            mock_pipeline.reset_mock()
            monitor.get_events_in_window(window_seconds=7200)
            wide = float(mock_pipeline.zcount.call_args_list[0][0][1][1:])

        assert wide < narrow

    def test_redis_error_propagates_to_caller(
        self, monitor: SafetyMonitor, mock_redis: MagicMock
    ) -> None:
        """Test Redis failures propagate so the health endpoint can degrade."""
        mock_redis.pipeline = MagicMock(side_effect=redis.RedisError("connection refused"))

        with pytest.raises(redis.RedisError):
            monitor.get_events_in_window(window_seconds=3600)

    def test_execute_error_propagates_to_caller(
        self, monitor: SafetyMonitor, mock_pipeline: MagicMock
    ) -> None:
        """Test a failure during execute() also propagates."""
        mock_pipeline.execute = MagicMock(side_effect=redis.ConnectionError("redis down"))

        with pytest.raises(redis.ConnectionError):
            monitor.get_events_in_window(window_seconds=3600)


@pytest.mark.unit
class TestLogEventWindowTracking:
    """Test suite for the rolling-window writes added to log_event."""

    @pytest.fixture
    def mock_redis(self) -> MagicMock:
        """Create a mock Redis client."""
        return MagicMock(spec=redis.Redis)

    @pytest.fixture
    def monitor(self, mock_redis: MagicMock) -> SafetyMonitor:
        """Create a SafetyMonitor instance with mocked Redis."""
        return SafetyMonitor(mock_redis)

    def test_event_added_to_rolling_window_sorted_set(
        self, monitor: SafetyMonitor, mock_redis: MagicMock
    ) -> None:
        """Test the event is scored by epoch seconds in the per-type sorted set."""
        with patch("safety.monitoring.time.time", return_value=FROZEN_NOW):
            monitor.log_event("pii_detected", {"field": "email"})

        mock_redis.zadd.assert_called_once()
        key, mapping = mock_redis.zadd.call_args[0]

        assert key == f"{RECENT_EVENTS_KEY_PREFIX}:pii_detected"
        assert list(mapping.values()) == [FROZEN_NOW]

    def test_repeated_events_use_unique_members(
        self, monitor: SafetyMonitor, mock_redis: MagicMock
    ) -> None:
        """Test identical events do not overwrite each other in the sorted set."""
        with patch("safety.monitoring.time.time", return_value=FROZEN_NOW):
            monitor.log_event("rate_limited", {"ip": "1.1.1.1"})
            monitor.log_event("rate_limited", {"ip": "1.1.1.1"})

        members = [member for call in mock_redis.zadd.call_args_list for member in call[0][1]]
        assert len(members) == 2
        assert len(set(members)) == 2, "ZADD members collided; one event would be lost"

    def test_aged_out_events_are_pruned(
        self, monitor: SafetyMonitor, mock_redis: MagicMock
    ) -> None:
        """Test events older than the retention period are removed."""
        with patch("safety.monitoring.time.time", return_value=FROZEN_NOW):
            monitor.log_event("injection_attempt", {"pattern": "ignore previous"})

        mock_redis.zremrangebyscore.assert_called_once()
        key, low, high = mock_redis.zremrangebyscore.call_args[0]

        assert key == f"{RECENT_EVENTS_KEY_PREFIX}:injection_attempt"
        assert low == 0
        assert high == FROZEN_NOW - EVENT_RETENTION_SECONDS

    def test_rolling_window_key_has_ttl(
        self, monitor: SafetyMonitor, mock_redis: MagicMock
    ) -> None:
        """Test the sorted set expires if events stop arriving."""
        monitor.log_event("bias_detected", {"term": "example"})

        ttls = [call[0][1] for call in mock_redis.expire.call_args_list]
        assert EVENT_RETENTION_SECONDS + 60 in ttls

    def test_invalid_event_type_is_not_recorded(
        self, monitor: SafetyMonitor, mock_redis: MagicMock
    ) -> None:
        """Test unknown event types never reach the sorted set."""
        monitor.log_event("not_a_real_type", {})

        mock_redis.zadd.assert_not_called()
        mock_redis.incr.assert_not_called()

    def test_redis_failure_during_log_is_swallowed(
        self, monitor: SafetyMonitor, mock_redis: MagicMock
    ) -> None:
        """Test logging an event never raises (logging must not break callers)."""
        mock_redis.zadd = MagicMock(side_effect=redis.RedisError("redis down"))

        with patch("safety.monitoring.logger"):
            monitor.log_event("content_filtered", {"reason": "toxicity"})


@pytest.mark.unit
class TestGetSafetyEventsLastHour:
    """Test suite for the module-level function the health endpoint imports."""

    @pytest.fixture
    def mock_redis(self) -> MagicMock:
        """Create a mock Redis client with a configurable pipeline."""
        client = MagicMock(spec=redis.Redis)
        client.pipeline.return_value.execute = MagicMock(return_value=[2, 0, 1, 0, 0])
        return client

    def test_uses_injected_client_without_touching_settings(self, mock_redis: MagicMock) -> None:
        """Test an injected client is used, so no live Redis is needed."""
        with patch("safety.monitoring._get_redis_client") as fallback:
            result = get_safety_events_last_hour(mock_redis)

        assert result == 3
        fallback.assert_not_called()

    def test_falls_back_to_shared_client(self, mock_redis: MagicMock) -> None:
        """Test the shared client is used when none is injected."""
        with patch("safety.monitoring._get_redis_client", return_value=mock_redis) as fallback:
            result = get_safety_events_last_hour()

        assert result == 3
        fallback.assert_called_once_with()

    def test_queries_the_one_hour_window(self, mock_redis: MagicMock) -> None:
        """Test the function counts over a one-hour window."""
        with patch("safety.monitoring.time.time", return_value=FROZEN_NOW):
            get_safety_events_last_hour(mock_redis)

        min_score = mock_redis.pipeline.return_value.zcount.call_args_list[0][0][1]
        assert float(min_score[1:]) == FROZEN_NOW - 3600

    def test_redis_error_propagates(self, mock_redis: MagicMock) -> None:
        """Test errors reach the caller; the health endpoint is what catches them."""
        mock_redis.pipeline.return_value.execute = MagicMock(
            side_effect=redis.ConnectionError("redis down")
        )

        with pytest.raises(redis.ConnectionError):
            get_safety_events_last_hour(mock_redis)
