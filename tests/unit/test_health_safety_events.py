"""Reproduction test for issue #68.

The /health endpoint should surface how many safety events were recorded in the
last hour so operators can monitor safety activity from the health check alone.

Today `api/routes/health.py` hardcodes `safety_events_last_hour` to 0 (see the
placeholder block at the end of `health_check`) and never calls
`safety.monitoring.SafetyMonitor.get_event_count`. This test records real safety
events through `SafetyMonitor` and asserts the health check reflects them.

It is expected to FAIL against the current code (health reports 0 instead of the
real count). The `xfail(strict=True)` marker documents the gap while keeping the
suite green; remove the marker once the fix wires SafetyMonitor into health.py.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from api.routes.health import health_check
from safety.monitoring import SafetyMonitor


def _fake_redis() -> Mock:
    """A minimal in-memory stand-in for the Redis counters SafetyMonitor uses."""
    store: dict[str, int] = {}
    r = Mock()
    r.incr = lambda key: store.__setitem__(key, store.get(key, 0) + 1)
    r.expire = Mock()
    r.get = lambda key: store.get(key)
    r.ping = Mock(return_value=True)
    return r


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=True,
    reason="issue #68: /health hardcodes safety_events_last_hour=0 and never "
    "queries SafetyMonitor. Remove this marker when the fix lands.",
)
async def test_health_surfaces_recorded_safety_events() -> None:
    # Arrange: eight safety events have been recorded in the monitoring system.
    redis_client = _fake_redis()
    monitor = SafetyMonitor(redis_client)
    for _ in range(5):
        monitor.log_event("pii_detected", {})
    for _ in range(3):
        monitor.log_event("injection_attempt", {})

    expected = sum(
        monitor.get_event_count(event_type) for event_type in SafetyMonitor.VALID_EVENT_TYPES
    )
    assert expected == 8, "sanity check: SafetyMonitor is the source of truth"

    # Act: hit the health check. Read the payload whether it returns 200 or
    # raises 503 (dependency health is irrelevant to this field).
    db = Mock()
    db.execute = AsyncMock(return_value=None)
    try:
        result = await health_check(db=db)
    except HTTPException as exc:
        result = exc.detail

    # Assert: the health check surfaces the real count, not a hardcoded 0.
    assert result["safety_events_last_hour"] == expected
