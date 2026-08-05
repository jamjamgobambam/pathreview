"""Regression tests for issue #68 — safety event count on the health check endpoint.

Issue: https://github.com/ascherj/pathreview/issues/68

Background
----------
The ``/health`` endpoint used to hardcode ``safety_events_last_hour`` to ``0`` and
never consult ``SafetyMonitor`` (the class that records safety events in Redis), so
the field never reflected real activity. This file started as the reproduction for
that bug; the fix wires the endpoint to ``SafetyMonitor.get_total_event_count()``,
and these tests now guard against a regression:

    * ``test_safety_monitor_actually_counts_events`` -- SafetyMonitor records events
      and can count them back.
    * ``test_health_endpoint_reports_recorded_safety_events`` -- the endpoint reports
      the recorded count instead of a hardcoded 0.
"""

import asyncio
from unittest.mock import patch

import pytest

from api.routes import health as health_mod
from safety.monitoring import SafetyMonitor


class FakeRedis:
    """Minimal in-memory stand-in for Redis (counters + ping)."""

    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key: str, seconds: int) -> None:
        pass

    def get(self, key: str):
        return self.store.get(key)

    def ping(self) -> bool:
        return True


class FakeDB:
    """Async DB stub so the endpoint's ``await db.execute(...)`` succeeds."""

    async def execute(self, query):
        return None


def _call_health(shared_redis: FakeRedis) -> dict:
    """Invoke the real health endpoint and return its status dict.

    Dependency health is irrelevant to this bug, so if the endpoint raises a 503
    we still return the payload (it is attached to the HTTPException's ``detail``).
    ``redis.Redis.from_url`` is patched to return ``shared_redis`` so the endpoint
    reads the same counters the test recorded events into.
    """
    from fastapi import HTTPException

    async def run() -> dict:
        with patch("redis.Redis.from_url", return_value=shared_redis):
            try:
                return await health_mod.health_check(db=FakeDB())
            except HTTPException as exc:
                return exc.detail  # payload still contains safety_events_last_hour

    return asyncio.run(run())


@pytest.mark.unit
def test_safety_monitor_actually_counts_events() -> None:
    """The data exists: SafetyMonitor records safety events and counts them back."""
    redis = FakeRedis()
    monitor = SafetyMonitor(redis)

    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("injection_attempt", {"pattern": "ignore previous"})
    monitor.log_event("pii_detected", {"field": "phone"})

    total = sum(monitor.get_event_count(t) for t in SafetyMonitor.VALID_EVENT_TYPES)
    assert total == 3


@pytest.mark.unit
def test_health_endpoint_reports_recorded_safety_events() -> None:
    """After safety events are recorded, /health reports them (not 0).

    Was the reproduction for issue #68 (previously xfail); now a regression test
    that passes because the endpoint reads the count from SafetyMonitor.
    """
    shared_redis = FakeRedis()
    monitor = SafetyMonitor(shared_redis)
    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("injection_attempt", {"pattern": "ignore previous"})
    recorded = sum(monitor.get_event_count(t) for t in SafetyMonitor.VALID_EVENT_TYPES)
    assert recorded == 2  # precondition: two real safety events exist

    health = _call_health(shared_redis)

    # The endpoint now surfaces the recorded events instead of a hardcoded 0.
    assert health["safety_events_last_hour"] == recorded
