"""Tests for safety event counting in the /health endpoint (issue #68).

`/health` should report the total number of safety events recorded by
`SafetyMonitor`, rather than the hardcoded 0 it returned before the fix.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from api.routes.health import health_check
from safety.monitoring import SafetyMonitor


def _fake_redis() -> Mock:
    """In-memory stand-in for the Redis counters SafetyMonitor uses."""
    store: dict[str, int] = {}
    client = Mock()
    client.incr = lambda key: store.__setitem__(key, store.get(key, 0) + 1)
    client.expire = Mock()
    client.get = lambda key: store.get(key)
    client.ping = Mock(return_value=True)
    return client


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_reports_total_safety_event_count() -> None:
    """/health sums recorded safety events across all event types."""
    redis_client = _fake_redis()
    monitor = SafetyMonitor(redis_client)
    for _ in range(5):
        monitor.log_event("pii_detected", {})
    for _ in range(3):
        monitor.log_event("injection_attempt", {})

    db = Mock()
    db.execute = AsyncMock(return_value=None)

    result = await health_check(db=db, redis_client=redis_client)

    assert result["safety_events_last_hour"] == 8


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_reports_zero_when_no_safety_events() -> None:
    """/health reports 0 safety events when none have been recorded."""
    redis_client = _fake_redis()

    db = Mock()
    db.execute = AsyncMock(return_value=None)

    result = await health_check(db=db, redis_client=redis_client)

    assert result["safety_events_last_hour"] == 0
