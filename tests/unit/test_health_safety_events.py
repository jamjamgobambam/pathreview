"""
Tests for issue D-08: "Add a safety event count to the health check endpoint."

The /health endpoint exposes a ``safety_events_last_hour`` field. It used to be
hardcoded to 0; it now reports the real total from ``SafetyMonitor``. These tests
cover the monitor's total-count helper and the endpoint wiring, including the
no-events and Redis-unavailable cases.

Unit tests: no external services — the DB is mocked and Redis is an in-memory fake.
"""

import asyncio
from unittest.mock import AsyncMock, patch

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


class BrokenRedis(FakeRedis):
    """A redis client whose reads fail, simulating an outage."""

    def get(self, key):
        raise ConnectionError("redis unavailable")


def _mock_db():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)
    return db


def _health_payload(db):
    """
    Return the /health payload whether the endpoint responds 200 or raises 503.

    (An unrelated config gap — health.py reads ``settings.redis_host``, which is
    not defined on Settings — marks the redis dependency unhealthy and makes the
    endpoint raise 503. The full status dict, including safety_events_last_hour,
    travels in the exception detail either way. That gap is out of scope for
    D-08; see PLAN.md.)
    """
    try:
        return asyncio.run(health_module.health_check(db=db))
    except HTTPException as exc:
        return exc.detail


# ── SafetyMonitor.get_total_event_count ──────────────────────────────────────


@pytest.mark.unit
def test_get_total_event_count_sums_across_types():
    monitor = SafetyMonitor(FakeRedis())
    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("pii_detected", {"field": "phone"})
    monitor.log_event("injection_attempt", {"pattern": "ignore previous"})
    monitor.log_event("bias_detected", {"term": "example"})

    assert monitor.get_total_event_count() == 4


@pytest.mark.unit
def test_get_total_event_count_zero_when_no_events():
    monitor = SafetyMonitor(FakeRedis())
    assert monitor.get_total_event_count() == 0


# ── /health endpoint wiring (D-08) ───────────────────────────────────────────


@pytest.mark.unit
def test_health_reports_recorded_safety_events():
    """
    The endpoint should report the safety-event total recorded in Redis.

    Regression for D-08: previously this field was hardcoded to 0 regardless of
    recorded events.
    """
    fake = FakeRedis()
    monitor = SafetyMonitor(fake)
    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("pii_detected", {"field": "phone"})
    monitor.log_event("injection_attempt", {"pattern": "ignore previous"})

    with patch("redis.from_url", return_value=fake):
        payload = _health_payload(_mock_db())

    assert payload["safety_events_last_hour"] == 3


@pytest.mark.unit
def test_health_safety_events_zero_when_no_events():
    with patch("redis.from_url", return_value=FakeRedis()):
        payload = _health_payload(_mock_db())

    assert payload["safety_events_last_hour"] == 0


@pytest.mark.unit
def test_health_safety_events_degrades_to_zero_when_redis_unavailable():
    """A Redis outage must not crash /health; the count degrades to 0."""
    with patch("redis.from_url", return_value=BrokenRedis()):
        payload = _health_payload(_mock_db())

    assert payload["safety_events_last_hour"] == 0
