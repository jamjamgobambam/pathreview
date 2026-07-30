"""Tests for health route."""

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from api.routes import health as health_routes
from safety.monitoring import SafetyMonitor

if TYPE_CHECKING:
    import redis


class DummyDB:
    """Minimal database stub for health route tests."""

    async def execute(self, query: str) -> None:
        """Simulate a successful database query."""
        return None


class FakeRedis:
    """Simple Redis stub used to avoid network access in tests."""

    def __init__(self) -> None:
        self.sorted_sets: dict[str, dict[str, float]] = {}

    def ping(self) -> bool:
        """Return a successful ping response."""
        return True

    def zadd(self, key: str, mapping: dict[str, float]) -> int:
        self.sorted_sets.setdefault(key, {}).update(mapping)
        return len(mapping)

    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        if key not in self.sorted_sets:
            return 0
        to_remove = [
            member for member, score in self.sorted_sets[key].items() if score <= max_score
        ]
        for member in to_remove:
            del self.sorted_sets[key][member]
        return len(to_remove)

    def zcount(self, key: str, min_score: float, max_score: float) -> int:
        entries = self.sorted_sets.get(key, {})
        return sum(1 for score in entries.values() if min_score <= score <= max_score)

    def expire(self, key: str, ttl: int) -> bool:
        return True


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test health route returns a healthy status with zero events."""
        monkeypatch.setattr("redis.from_url", lambda *args, **kwargs: FakeRedis())
        monkeypatch.setattr(
            "safety.monitoring.SafetyMonitor.get_total_event_count",
            lambda self, window_hours=1: 0,
        )

        response = await health_routes.health_check(DummyDB())

        assert response["status"] == "healthy"
        assert response["dependencies"]["postgres"] == "healthy"
        assert response["dependencies"]["redis"] == "healthy"
        assert response["safety_events_last_hour"] == 0

    @pytest.mark.asyncio
    async def test_health_check_returns_real_safety_event_count(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test health route returns the real rolling safety-event count."""
        monkeypatch.setattr("redis.from_url", lambda *args, **kwargs: FakeRedis())
        monkeypatch.setattr(
            "safety.monitoring.SafetyMonitor.get_total_event_count",
            lambda self, window_hours=1: 3,
        )

        response = await health_routes.health_check(DummyDB())

        assert response["safety_events_last_hour"] == 3

    def test_monitoring_uses_a_rolling_one_hour_window(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Rolling counts should exclude events older than one hour."""
        fake_redis = FakeRedis()
        monitor = SafetyMonitor(cast("redis.Redis", fake_redis))
        timestamps = iter([1000.0, 1000.0, 100.0, 4000.0])
        monkeypatch.setattr("safety.monitoring.time.time", lambda: next(timestamps))

        monitor.log_event("pii_detected", {"source": "test"})
        monitor.log_event("pii_detected", {"source": "test"})
        monitor.log_event("pii_detected", {"source": "test"})

        assert monitor.get_event_count("pii_detected", window_hours=1) == 2

    def test_log_event_stores_timestamped_entries(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Logged events should be stored as timestamped sorted-set entries."""
        fake_redis = FakeRedis()
        monitor = SafetyMonitor(cast("redis.Redis", fake_redis))
        monkeypatch.setattr("safety.monitoring.time.time", lambda: 1700000000.0)
        monkeypatch.setattr("safety.monitoring.uuid.uuid4", lambda: SimpleNamespace(hex="abc123"))

        monitor.log_event("pii_detected", {"source": "test"})

        entries = fake_redis.sorted_sets["safety:events:pii_detected"]
        assert len(entries) == 1
        member, score = next(iter(entries.items()))
        assert score == 1700000000.0
        assert member == "1700000000.0:abc123"

    @pytest.mark.asyncio
    async def test_health_check_populates_safety_count_field(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The health endpoint should expose the computed safety event count."""
        monkeypatch.setattr("redis.from_url", lambda *args, **kwargs: FakeRedis())
        monkeypatch.setattr(
            "safety.monitoring.SafetyMonitor.get_total_event_count",
            lambda self, window_hours=1: 7,
        )

        response = await health_routes.health_check(DummyDB())

        assert response["safety_events_last_hour"] == 7
