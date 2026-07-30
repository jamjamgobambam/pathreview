"""Tests for health route."""

import pytest

from api.routes import health as health_routes


class DummyDB:
    """Minimal database stub for health route tests."""

    async def execute(self, query: str) -> None:
        """Simulate a successful database query."""
        return None


class FakeRedis:
    """Simple Redis stub used to avoid network access in tests."""

    def ping(self) -> bool:
        """Return a successful ping response."""
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
