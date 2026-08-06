"""Unit tests for the /health endpoint.

These tests are fully isolated from external services: Redis and
PostgreSQL are both faked, so the suite runs anywhere (including CI)
without any real infrastructure and without depending on ambient state
left over from previous test runs.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.database import get_db
from safety.monitoring import SafetyMonitor

client = TestClient(app)


class FakeRedis:
    """Minimal in-memory stand-in for the subset of redis-py used by
    SafetyMonitor (ZADD/ZREMRANGEBYSCORE/EXPIRE/ZCOUNT + pipelines).

    This isn't a general-purpose fake — it implements just enough to
    exercise the real SafetyMonitor logic without needing a live Redis
    server or the `fakeredis` package.
    """

    def __init__(self) -> None:
        self._zsets: dict[str, dict[str, float]] = {}

    def ping(self) -> bool:
        return True

    def zadd(self, key: str, mapping: dict[str, float]) -> None:
        self._zsets.setdefault(key, {}).update(mapping)

    def zremrangebyscore(self, key: str, min_: float, max_: float) -> None:
        z = self._zsets.get(key, {})
        for member in [m for m, score in z.items() if min_ <= score <= max_]:
            del z[member]

    def expire(self, key: str, ttl: int) -> None:
        pass  # no-op; not relevant to correctness of counting logic

    def zcount(self, key: str, min_: float, max_: float) -> int:
        if max_ == "+inf":
            max_ = float("inf")
        z = self._zsets.get(key, {})
        return sum(1 for score in z.values() if min_ <= score <= max_)

    def pipeline(self) -> "FakePipeline":
        return FakePipeline(self)


class FakePipeline:
    """Fakes redis-py's pipeline(): batches calls, executes them together."""

    def __init__(self, redis_client: FakeRedis) -> None:
        self._redis = redis_client
        self._ops: list[tuple] = []

    def zadd(self, key: str, mapping: dict[str, float]) -> "FakePipeline":
        self._ops.append(("zadd", key, mapping))
        return self

    def zremrangebyscore(self, key: str, min_: float, max_: float) -> "FakePipeline":
        self._ops.append(("zremrangebyscore", key, min_, max_))
        return self

    def expire(self, key: str, ttl: int) -> "FakePipeline":
        self._ops.append(("expire", key, ttl))
        return self

    def zcount(self, key: str, min_: float, max_: float) -> "FakePipeline":
        self._ops.append(("zcount", key, min_, max_))
        return self

    def execute(self) -> list:
        results = []
        for op in self._ops:
            name, key, *args = op
            result = getattr(self._redis, name)(key, *args)
            results.append(result)
        return results


class FakeDB:
    """Fakes the async DB session used by the postgres health check."""

    async def execute(self, query):
        return True


async def _override_get_db():
    yield FakeDB()


@pytest.fixture(autouse=True)
def override_dependencies():
    """Swap the real Postgres dependency for a fake one on every test."""
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def fake_redis():
    """A fresh FakeRedis instance per test, so tests don't leak state
    into each other the way the real-Redis version did.
    """
    return FakeRedis()


def test_health_endpoint_returns_exact_safety_event_count(fake_redis):
    """Logs a known number of events and asserts the exact count, not
    just `>= N` — a loose `>=` check wouldn't catch double-counting.
    """
    monitor = SafetyMonitor(fake_redis)
    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("injection_attempt", {"payload": "DROP TABLE"})
    monitor.log_event("pii_detected", {"field": "phone"})

    with patch("redis.from_url", return_value=fake_redis):
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["safety_events_last_24h"] == 3


def test_health_endpoint_does_not_double_count(fake_redis):
    """Regression guard: logging events across multiple categories should
    sum to exactly their total, not more (e.g. from a pipeline bug that
    executes a write twice).
    """
    monitor = SafetyMonitor(fake_redis)
    for _ in range(2):
        monitor.log_event("pii_detected", {"field": "email"})
    for _ in range(5):
        monitor.log_event("rate_limited", {"ip": "127.0.0.1"})

    with patch("redis.from_url", return_value=fake_redis):
        response = client.get("/health")

    assert response.json()["safety_events_last_24h"] == 7


def test_health_endpoint_with_no_events_returns_zero(fake_redis):
    """No events logged at all (missing/non-existent keys) -> 0, not an error."""
    with patch("redis.from_url", return_value=fake_redis):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["safety_events_last_24h"] == 0


def test_health_endpoint_falls_back_to_zero_when_redis_unreachable():
    """If Redis can't be reached, the endpoint should degrade gracefully:
    report redis as unhealthy and safety_events_last_24h as 0, rather
    than raising an unhandled exception.
    """
    with patch("redis.from_url", side_effect=ConnectionError("Connection refused")):
        response = client.get("/health")

    # Redis being down makes the overall health status unhealthy (503),
    # but the response body should still be well-formed.
    assert response.status_code == 503
    data = response.json()["detail"]
    assert data["dependencies"]["redis"] == "unhealthy"
    assert data["safety_events_last_24h"] == 0
