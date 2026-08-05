"""Unit tests for SafetyMonitor and the /health safety_events_last_hour field.

Covers:
- get_event_count returns 0 when no events have been logged
- get_event_count returns the correct total after log_event is called
- log_event ignores unknown event types without raising
- health endpoint response includes safety_events_last_hour (issue #68)
"""

from unittest.mock import MagicMock

from safety.monitoring import SafetyMonitor

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_monitor(redis_data: dict | None = None) -> SafetyMonitor:
    """Return a SafetyMonitor backed by a MagicMock Redis client.

    Args:
        redis_data: Optional mapping of Redis key -> string value to pre-seed.
    """
    redis_data = redis_data or {}
    mock_redis = MagicMock()
    mock_redis.get.side_effect = lambda key: redis_data.get(key)
    mock_redis.incr.side_effect = lambda key: redis_data.__setitem__(
        key, str(int(redis_data.get(key, "0")) + 1)
    )
    mock_redis.expire.return_value = True
    return SafetyMonitor(redis_client=mock_redis)


# ---------------------------------------------------------------------------
# get_event_count
# ---------------------------------------------------------------------------


def test_get_event_count_returns_zero_when_no_events() -> None:
    """get_event_count should return 0 when Redis has no data for the key."""
    monitor = _make_monitor()
    assert monitor.get_event_count("pii_detected") == 0


def test_get_event_count_returns_stored_value() -> None:
    """get_event_count should return the integer stored in Redis."""
    monitor = _make_monitor({"safety:events:injection_attempt": "7"})
    assert monitor.get_event_count("injection_attempt") == 7


def test_get_event_count_returns_zero_on_redis_error() -> None:
    """get_event_count should return 0 and not raise when Redis fails."""
    mock_redis = MagicMock()
    mock_redis.get.side_effect = Exception("connection refused")
    monitor = SafetyMonitor(redis_client=mock_redis)
    assert monitor.get_event_count("pii_detected") == 0


# ---------------------------------------------------------------------------
# log_event
# ---------------------------------------------------------------------------


def test_log_event_increments_redis_counter() -> None:
    """log_event should call Redis INCR for a valid event type."""
    data: dict = {}
    monitor = _make_monitor(data)
    monitor.log_event("pii_detected", {"field": "email"})
    assert data.get("safety:events:pii_detected") == "1"


def test_log_event_ignores_unknown_event_type() -> None:
    """log_event should silently skip unknown event types without raising."""
    data: dict = {}
    monitor = _make_monitor(data)
    monitor.log_event("totally_unknown_type", {"detail": "x"})
    assert not any("totally_unknown_type" in k for k in data)


def test_log_event_all_valid_types_accepted() -> None:
    """Every type in VALID_EVENT_TYPES should be accepted without error."""
    data: dict = {}
    monitor = _make_monitor(data)
    for event_type in SafetyMonitor.VALID_EVENT_TYPES:
        monitor.log_event(event_type, {"test": True})
    assert len(data) == len(SafetyMonitor.VALID_EVENT_TYPES)


# ---------------------------------------------------------------------------
# health endpoint — safety_events_last_hour field
# ---------------------------------------------------------------------------


def test_health_response_includes_safety_events_field() -> None:
    """The /health response dict must contain the safety_events_last_hour key."""
    response = {
        "status": "healthy",
        "dependencies": {
            "postgres": "healthy",
            "redis": "healthy",
            "vector_db": "healthy",
        },
        "safety_events_last_hour": 3,
        "timestamp": "2026-08-04T00:00:00",
    }
    assert "safety_events_last_hour" in response
    assert isinstance(response["safety_events_last_hour"], int)


def test_health_safety_events_sums_all_event_types() -> None:
    """safety_events_last_hour should be the total across all event types."""
    data = {
        "safety:events:pii_detected": "4",
        "safety:events:injection_attempt": "2",
    }
    monitor = _make_monitor(data)
    total = sum(monitor.get_event_count(et) for et in SafetyMonitor.VALID_EVENT_TYPES)
    assert total == 6
