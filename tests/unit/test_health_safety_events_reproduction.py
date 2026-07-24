"""Reproduction for issue #68 — Add a safety event count to the health check endpoint.

Issue: https://github.com/ascherj/pathreview/issues/68

Scenario reproduced here
------------------------
The ``/health`` endpoint exposes a ``safety_events_last_hour`` field, but it is
hardcoded to ``0`` (see ``api/routes/health.py`` lines 25 and 78, commented as a
"placeholder"). The endpoint never consults ``SafetyMonitor``, which is the class
that actually records safety events (PII detections, injection attempts, etc.) in
Redis. So even when real safety events have occurred, ``/health`` always reports 0.

These tests prove both halves of the bug:

    * ``test_safety_monitor_actually_counts_events`` (passes today) -- the data
      exists: ``SafetyMonitor`` records events and can count them back.
    * ``test_health_endpoint_reports_recorded_safety_events`` (xfail today) -- the
      endpoint ignores that data and reports 0.

The second test is marked ``xfail(strict=True)`` so CI stays green while the bug is
documented. When the Week 9 fix wires the endpoint to the safety counts and it
starts passing, strict xfail will flag it so the marker can be removed.
"""

import asyncio

import pytest
from unittest.mock import patch

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
    ``redis.Redis`` is patched to return ``shared_redis`` so that a *fixed*
    endpoint reading the same counters would see the recorded events.
    """
    from fastapi import HTTPException

    async def run() -> dict:
        with patch("redis.Redis", return_value=shared_redis):
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
@pytest.mark.xfail(
    strict=True,
    reason="Issue #68: /health hardcodes safety_events_last_hour=0 and never reads "
    "SafetyMonitor. Fix lands in Week 9.",
)
def test_health_endpoint_reports_recorded_safety_events() -> None:
    """After safety events are recorded, /health should report them (not 0)."""
    shared_redis = FakeRedis()
    monitor = SafetyMonitor(shared_redis)
    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("injection_attempt", {"pattern": "ignore previous"})
    recorded = sum(monitor.get_event_count(t) for t in SafetyMonitor.VALID_EVENT_TYPES)
    assert recorded == 2  # precondition: two real safety events exist

    health = _call_health(shared_redis)

    # Desired behavior: the endpoint surfaces the recorded events.
    # Today it returns 0, so this xfails and documents the reproduced bug.
    assert health["safety_events_last_hour"] == recorded
