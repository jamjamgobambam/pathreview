"""
Reproduction test for issue D-08:
"Add a safety event count to the health check endpoint."

The /health endpoint exposes a `safety_events_last_hour` field, but
api/routes/health.py hardcodes it to 0 (line ~78, "This would be populated by
actual safety event logging") and never queries SafetyMonitor. So no matter how
many safety events are recorded, /health always reports 0.

This test demonstrates the gap: it records safety events through SafetyMonitor
(proving the count data is available via get_event_count), then calls the real
health_check endpoint and asserts the reported count matches. It FAILS on the
current code because the endpoint returns 0 regardless.

Unit test: no external services — the DB is mocked and Redis is an in-memory fake.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

import api.routes.health as health_module
from safety.monitoring import SafetyMonitor


class FakeRedis:
    """Minimal in-memory stand-in for the redis client SafetyMonitor uses."""

    def __init__(self):
        self.store = {}

    def incr(self, key):
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key, seconds):
        return True

    def get(self, key):
        val = self.store.get(key)
        return None if val is None else str(val).encode()

    def ping(self):
        return True


def _health_payload(db):
    """
    Return the health payload whether the endpoint responds 200 or raises 503.

    (On the current code an unrelated config gap marks Redis unhealthy and the
    endpoint raises 503, but the full status dict — including
    safety_events_last_hour — travels in the exception detail either way.)
    """
    try:
        return asyncio.run(health_module.health_check(db=db))
    except HTTPException as exc:
        return exc.detail


@pytest.mark.unit
def test_health_reports_recorded_safety_events():
    # Record 3 safety events through the monitor.
    fake_redis = FakeRedis()
    monitor = SafetyMonitor(fake_redis)
    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("pii_detected", {"field": "phone"})
    monitor.log_event("injection_attempt", {"pattern": "ignore previous"})

    # The count data IS available from the monitor.
    recorded = sum(
        monitor.get_event_count(event_type)
        for event_type in SafetyMonitor.VALID_EVENT_TYPES
    )
    assert recorded == 3, "sanity check: SafetyMonitor should have 3 events"

    # But the health endpoint ignores it and always reports 0.
    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)
    payload = _health_payload(db)

    assert payload["safety_events_last_hour"] == recorded, (
        "health endpoint reports "
        f"{payload['safety_events_last_hour']} safety events, "
        f"but {recorded} were recorded (endpoint hardcodes 0 — issue D-08)"
    )
