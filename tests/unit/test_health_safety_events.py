"""Reproduction tests for issue #68.

Add a safety event count to the health check endpoint.

The `/health` endpoint advertises a ``safety_events_last_hour`` field, but it is
hardcoded to ``0`` in ``api/routes/health.py`` (see the "placeholder" comment).
Meanwhile ``safety/monitoring.py`` already tracks real per-type counts in Redis
via ``SafetyMonitor.get_event_count``. These tests document that disconnect:
the data source works, but the endpoint never consults it.

In Week 9 the second test's expectation flips from "hardcoded 0" to "reflects
the SafetyMonitor count" once the endpoint is wired up.
"""

from unittest.mock import MagicMock, patch

import pytest

import api.routes.health as health_module
from safety.monitoring import SafetyMonitor


class FakeRedis:
    """Minimal in-memory stand-in for the Redis counter operations used by
    ``SafetyMonitor`` (``incr``/``expire``/``get``)."""

    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.store[key] = int(self.store.get(key, 0)) + 1
        return self.store[key]

    def expire(self, key: str, ttl: int) -> None:  # noqa: ARG002 - ttl unused in fake
        pass

    def get(self, key: str):
        return self.store.get(key)


@pytest.mark.unit
def test_safety_monitor_tracks_real_counts():
    """The data source works: logged events produce a real, non-zero count.

    This is the value the health endpoint *should* be surfacing.
    """
    monitor = SafetyMonitor(FakeRedis())

    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("pii_detected", {"field": "phone"})
    monitor.log_event("injection_attempt", {"source": "prompt"})

    assert monitor.get_event_count("pii_detected") == 2
    assert monitor.get_event_count("injection_attempt") == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_endpoint_hardcodes_zero_safety_events():
    """Reproduction of the bug: `/health` reports 0 regardless of real activity.

    The endpoint's ``safety_events_last_hour`` field is read whether the overall
    status is healthy (returns a dict) or unhealthy (raises HTTPException whose
    ``detail`` carries the same dict). Either way, even though SafetyMonitor
    would report non-zero counts (see the test above), the value is the
    hardcoded placeholder.
    """
    from unittest.mock import AsyncMock

    from fastapi import HTTPException

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=None)

    fake_redis = MagicMock()
    fake_redis.ping.return_value = True

    with patch("redis.Redis", return_value=fake_redis):
        try:
            result = await health_module.health_check(db=mock_db)
        except HTTPException as exc:
            result = exc.detail

    # BUG (#68): always 0 — the endpoint never calls SafetyMonitor.get_event_count.
    assert result["safety_events_last_hour"] == 0
