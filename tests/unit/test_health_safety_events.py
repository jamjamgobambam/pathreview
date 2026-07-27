"""Reproduction tests for issue #68 — safety event count in the health check.

https://github.com/ascherj/pathreview/issues/68

The /health endpoint returns a `safety_events_last_hour` field, but it is
hardcoded to 0 (api/routes/health.py) and never consults the safety subsystem.
`SafetyMonitor` (safety/monitoring.py) already records per-type counts in Redis,
so the data exists — it just isn't surfaced.

`test_safety_monitor_records_event_counts` PASSES today (proving the data source
works). `test_health_surfaces_real_safety_event_count` FAILS today (it is the
reproduction of the bug) and should pass once the fix wires the endpoint to the
monitor in Week 9.
"""

import asyncio
from unittest.mock import patch

import pytest

from safety.monitoring import SafetyMonitor


class FakeRedis:
    """Minimal in-memory stand-in for the pieces SafetyMonitor/health use."""

    def __init__(self):
        self.store = {}

    def ping(self):
        return True

    def incr(self, key):
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key, seconds):
        pass

    def get(self, key):
        value = self.store.get(key)
        return str(value) if value is not None else None


class FakeDB:
    """Async DB session whose execute() is awaitable, for the postgres check."""

    async def execute(self, query):
        return None


def _call_health(redis_client):
    """Call the real health endpoint, returning its payload.

    The endpoint raises HTTPException(503) when a dependency check fails; in that
    case the payload is carried on `.detail`. Either way we return the dict so the
    test can inspect `safety_events_last_hour`.
    """
    from api.routes import health
    from fastapi import HTTPException

    with patch("redis.Redis", lambda *a, **k: redis_client):
        try:
            return asyncio.run(health.health_check(db=FakeDB()))
        except HTTPException as exc:
            return exc.detail


@pytest.mark.unit
class TestHealthSafetyEvents:
    """Issue #68 reproduction."""

    def test_safety_monitor_records_event_counts(self):
        """The safety layer already tracks real per-type counts in Redis."""
        redis_client = FakeRedis()
        monitor = SafetyMonitor(redis_client)

        monitor.log_event("pii_detected", {})
        monitor.log_event("injection_attempt", {})
        monitor.log_event("pii_detected", {})

        total = sum(
            monitor.get_event_count(event_type)
            for event_type in SafetyMonitor.VALID_EVENT_TYPES
        )
        assert total == 3

    def test_health_surfaces_real_safety_event_count(self):
        """/health should report the real number of recent safety events.

        REPRODUCTION (issue #68): currently fails — the endpoint hardcodes 0, so it
        reports 0 even though three safety events were recorded.
        """
        redis_client = FakeRedis()
        monitor = SafetyMonitor(redis_client)
        monitor.log_event("pii_detected", {})
        monitor.log_event("injection_attempt", {})
        monitor.log_event("pii_detected", {})

        payload = _call_health(redis_client)

        assert payload["safety_events_last_hour"] == 3
