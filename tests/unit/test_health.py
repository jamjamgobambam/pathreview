"""Tests for the /health endpoint safety event count."""

import time
from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import api.main as main_module
from api.deps import get_safety_monitor
from api.main import app
from core.database import get_db
from safety.monitoring import SafetyMonitor


class FakeRedis:
    """Minimal in-memory stand-in for the sorted-set operations we use."""

    def __init__(self) -> None:
        self.store: dict[str, dict[str, float]] = {}

    def zadd(self, key: str, mapping: dict[str, float]) -> None:
        self.store.setdefault(key, {}).update(mapping)

    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> None:
        bucket = self.store.get(key, {})
        self.store[key] = {m: s for m, s in bucket.items() if not (min_score <= s <= max_score)}

    def zcard(self, key: str) -> int:
        return len(self.store.get(key, {}))

    def expire(self, key: str, seconds: int) -> None:
        pass


@pytest.fixture(autouse=True)
def skip_real_db_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent the app's real startup event from touching Postgres,
    and work around the pre-existing missing redis_host/redis_port settings."""

    async def noop() -> None:
        pass

    monkeypatch.setattr(main_module, "init_db", noop)

    from core.config import settings

    monkeypatch.setattr(type(settings), "redis_host", "localhost", raising=False)
    monkeypatch.setattr(type(settings), "redis_port", 6379, raising=False)


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def safety_monitor(fake_redis: FakeRedis) -> SafetyMonitor:
    return SafetyMonitor(fake_redis)  # type: ignore[arg-type]


@pytest.fixture
def client(safety_monitor: SafetyMonitor) -> Generator[TestClient, None, None]:
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=None)

    async def override_get_db() -> Generator[AsyncMock, None, None]:  # type: ignore[misc]
        yield mock_db

    app.dependency_overrides[get_safety_monitor] = lambda: safety_monitor
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health_reflects_recent_safety_events(
    client: TestClient, safety_monitor: SafetyMonitor
) -> None:
    safety_monitor.log_event("content_filtered", {"reason": "test"})
    safety_monitor.log_event("rate_limited", {"reason": "test"})

    response = client.get("/health")

    assert response.json()["safety_events_last_hour"] == 2


def test_health_no_events_returns_zero(client: TestClient) -> None:
    response = client.get("/health")
    assert response.json()["safety_events_last_hour"] == 0


def test_health_events_outside_window_not_counted(
    safety_monitor: SafetyMonitor, client: TestClient
) -> None:
    key = "safety:events:pii_detected:zset"
    old_timestamp = time.time() - (2 * 3600)  # 2 hours ago
    safety_monitor.redis.zadd(key, {"old-event": old_timestamp})

    response = client.get("/health")

    assert response.json()["safety_events_last_hour"] == 0


def test_health_multiple_event_types_summed(
    safety_monitor: SafetyMonitor, client: TestClient
) -> None:
    safety_monitor.log_event("pii_detected", {})
    safety_monitor.log_event("injection_attempt", {})
    safety_monitor.log_event("bias_detected", {})

    response = client.get("/health")

    assert response.json()["safety_events_last_hour"] == 3


def test_health_redis_down_falls_back_to_zero(
    client: TestClient, safety_monitor: SafetyMonitor
) -> None:
    def broken_zcard(key: str) -> int:
        raise ConnectionError("redis down")

    safety_monitor.redis.zcard = broken_zcard  # type: ignore[method-assign, assignment]

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["safety_events_last_hour"] == 0
