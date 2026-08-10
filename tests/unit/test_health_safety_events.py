"""Tests for the safety event count in the health check endpoint (issue #68).

https://github.com/ascherj/pathreview/issues/68

The /health endpoint exposes a `safety_events_last_hour` field. It used to be
hardcoded to 0; it now surfaces the real count recorded by `SafetyMonitor`
(safety/monitoring.py), which increments per-type counters in Redis.

These tests exercise the real endpoint (`api.routes.health.health_check`) with an
in-memory fake Redis:
- the safety layer records counts,
- /health reports the summed count,
- and a Redis failure degrades the count to 0 without breaking the check.
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


class BrokenRedis:
    """A Redis client that fails on every operation (simulates Redis down)."""

    def ping(self):
        raise ConnectionError("redis unavailable")

    def incr(self, key):
        raise ConnectionError("redis unavailable")

    def expire(self, key, seconds):
        raise ConnectionError("redis unavailable")

    def get(self, key):
        raise ConnectionError("redis unavailable")


class FakeDB:
    """Async DB session whose execute() is awaitable, for the postgres check."""

    async def execute(self, query):
        return None


def _call_health(redis_client):
    """Call the real health endpoint, returning its payload.

    The endpoint builds its safety Redis client via `redis.Redis.from_url`, so we
    patch that to return our fake. The endpoint raises HTTPException(503) when a
    dependency check fails; in that case the payload is carried on `.detail`. Either
    way we return the dict so the test can inspect `safety_events_last_hour`.
    """
    from fastapi import HTTPException

    from api.routes import health

    with patch("redis.Redis.from_url", lambda *a, **k: redis_client):
        try:
            return asyncio.run(health.health_check(db=FakeDB()))
        except HTTPException as exc:
            return exc.detail


@pytest.mark.unit
class TestHealthSafetyEvents:
    """Issue #68 — safety event count in the health check."""

    def test_safety_monitor_records_event_counts(self):
        """The safety layer tracks real per-type counts in Redis."""
        redis_client = FakeRedis()
        monitor = SafetyMonitor(redis_client)

        monitor.log_event("pii_detected", {})
        monitor.log_event("injection_attempt", {})
        monitor.log_event("pii_detected", {})

        assert monitor.get_total_event_count() == 3

    def test_health_surfaces_real_safety_event_count(self):
        """/health reports the real number of recent safety events, not a constant 0."""
        redis_client = FakeRedis()
        monitor = SafetyMonitor(redis_client)
        monitor.log_event("pii_detected", {})
        monitor.log_event("injection_attempt", {})
        monitor.log_event("pii_detected", {})

        payload = _call_health(redis_client)

        assert payload["safety_events_last_hour"] == 3

    def test_health_reports_zero_when_no_events(self):
        """With no events recorded, the count is 0."""
        payload = _call_health(FakeRedis())

        assert payload["safety_events_last_hour"] == 0

    def test_health_safety_count_degrades_when_redis_unavailable(self):
        """A Redis failure leaves the count at 0 and never breaks the health check."""
        payload = _call_health(BrokenRedis())

        assert payload["safety_events_last_hour"] == 0
