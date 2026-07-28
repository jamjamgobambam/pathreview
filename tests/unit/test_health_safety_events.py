"""Tests for issue #68.

Add a safety event count to the health check endpoint.

The `/health` endpoint advertises a ``safety_events_last_hour`` field that used
to be hardcoded to ``0`` in ``api/routes/health.py``, even though
``safety/monitoring.py`` already tracked real per-type counts in Redis via
``SafetyMonitor.get_event_count``. These tests cover the wiring that closes that
gap: the aggregation helper ``SafetyMonitor.get_total_event_count`` and the
endpoint now reporting its value instead of a placeholder.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import api.routes.health as health_module
from safety.monitoring import SafetyMonitor


class FakeRedis:
    """Minimal in-memory stand-in for the Redis operations used by
    ``SafetyMonitor`` (``incr``/``expire``/``get``) and by the endpoint's Redis
    health check (``ping``)."""

    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.store[key] = int(self.store.get(key, 0)) + 1
        return self.store[key]

    def expire(self, key: str, ttl: int) -> None:  # noqa: ARG002 - ttl unused in fake
        pass

    def get(self, key: str):
        return self.store.get(key)

    def ping(self) -> bool:
        return True


async def call_health_check(redis_client) -> dict:
    """Call the health endpoint with a stubbed DB and the given Redis client.

    Args:
        redis_client: Object returned by the patched ``redis.from_url``

    Returns:
        The health payload, whether the endpoint returned it directly or raised
        an ``HTTPException`` whose ``detail`` carries the same dict.
    """
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=None)

    with patch("redis.from_url", return_value=redis_client):
        try:
            return await health_module.health_check(db=mock_db)
        except HTTPException as exc:
            return exc.detail


@pytest.mark.unit
def test_safety_monitor_tracks_real_counts():
    """The data source works: logged events produce a real, non-zero count."""
    monitor = SafetyMonitor(FakeRedis())

    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("pii_detected", {"field": "phone"})
    monitor.log_event("injection_attempt", {"source": "prompt"})

    assert monitor.get_event_count("pii_detected") == 2
    assert monitor.get_event_count("injection_attempt") == 1


@pytest.mark.unit
def test_get_total_event_count_sums_all_event_types():
    """The aggregation helper sums counters across every valid event type."""
    monitor = SafetyMonitor(FakeRedis())

    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("pii_detected", {"field": "phone"})
    monitor.log_event("injection_attempt", {"source": "prompt"})
    monitor.log_event("rate_limited", {"user": "u1"})

    assert monitor.get_total_event_count() == 4


@pytest.mark.unit
def test_get_total_event_count_with_no_events():
    """No events logged yet (counters absent or expired) totals to 0."""
    assert SafetyMonitor(FakeRedis()).get_total_event_count() == 0


@pytest.mark.unit
def test_get_total_event_count_ignores_unknown_event_types():
    """Only counters for VALID_EVENT_TYPES are summed."""
    fake_redis = FakeRedis()
    fake_redis.store["safety:events:legacy_event"] = 99

    monitor = SafetyMonitor(fake_redis)
    monitor.log_event("bias_detected", {"axis": "gender"})

    assert monitor.get_total_event_count() == 1


@pytest.mark.unit
def test_get_total_event_count_returns_zero_on_redis_error():
    """A Redis failure degrades the total to 0 instead of raising."""
    failing_redis = MagicMock()
    failing_redis.get.side_effect = ConnectionError("redis is down")

    assert SafetyMonitor(failing_redis).get_total_event_count() == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_endpoint_reports_real_safety_event_count():
    """Fix for #68: `/health` surfaces the aggregated SafetyMonitor count."""
    fake_redis = FakeRedis()
    monitor = SafetyMonitor(fake_redis)
    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("pii_detected", {"field": "phone"})
    monitor.log_event("content_filtered", {"reason": "toxicity"})

    result = await call_health_check(fake_redis)

    assert result["safety_events_last_hour"] == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_endpoint_reports_zero_when_no_safety_events():
    """A quiet safety layer still reports 0 — the field stays an integer."""
    result = await call_health_check(FakeRedis())

    assert result["safety_events_last_hour"] == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_endpoint_survives_redis_outage():
    """Redis being down marks the dependency unhealthy but never raises out of
    the safety count: the field falls back to 0."""
    failing_redis = MagicMock()
    failing_redis.ping.side_effect = ConnectionError("connection refused")

    result = await call_health_check(failing_redis)

    assert result["safety_events_last_hour"] == 0
    assert result["dependencies"]["redis"] == "unhealthy"
