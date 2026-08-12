"""Tests for the health endpoint (Issue #68: safety_events_last_hour)"""

from collections.abc import AsyncGenerator, Generator
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import health as health_route
from core.database import get_db

# Stand-in for core.config.settings. The endpoint resolves settings at call
# time (`from core.config import settings` inside the function body), so
# patching the module attribute is enough and no real services are contacted.
FAKE_SETTINGS = SimpleNamespace(
    redis_host="localhost",
    redis_port=6379,
    redis_url="redis://localhost:6379/0",
    vector_db_url="http://localhost:8001",
)


class StubSession:
    """Minimal async DB session that satisfies the postgres liveness probe."""

    async def execute(self, *args: Any, **kwargs: Any) -> None:
        return None


async def override_get_db() -> AsyncGenerator[StubSession, None]:
    """Dependency override that avoids a live PostgreSQL connection."""
    yield StubSession()


@pytest.mark.unit
class TestHealthSafetyEventCount:
    """Test suite for the safety_events_last_hour field on GET /health."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Build a minimal app with only the health router mounted."""
        app = FastAPI()
        app.include_router(health_route.router)
        app.dependency_overrides[get_db] = override_get_db
        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create a TestClient for the isolated app."""
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def healthy_dependencies(self) -> Generator[None, None, None]:
        """Make postgres/redis/vector_db report healthy without live services."""
        with patch("core.config.settings", FAKE_SETTINGS), patch("redis.Redis", MagicMock()):
            yield

    def test_success_state_reports_event_count(self, client: TestClient) -> None:
        """Test a successful count is surfaced in the response payload."""
        with patch.object(health_route, "get_safety_events_last_hour", return_value=3) as counter:
            response = client.get("/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["safety_events_last_hour"] == 3
        counter.assert_called_once_with()

    def test_zero_events_reported_as_zero(self, client: TestClient) -> None:
        """Test a quiet hour reports 0 rather than null."""
        with patch.object(health_route, "get_safety_events_last_hour", return_value=0):
            response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["safety_events_last_hour"] == 0

    def test_fault_tolerance_degrades_to_null(self, client: TestClient) -> None:
        """Test a monitoring failure yields null instead of failing the check."""
        with patch.object(
            health_route,
            "get_safety_events_last_hour",
            side_effect=Exception("monitoring unreachable"),
        ):
            response = client.get("/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["safety_events_last_hour"] is None
        assert "safety_events_last_hour" in payload

    def test_monitoring_failure_does_not_change_overall_status(self, client: TestClient) -> None:
        """Test the endpoint stays healthy when only monitoring is broken."""
        with patch.object(
            health_route,
            "get_safety_events_last_hour",
            side_effect=Exception("monitoring unreachable"),
        ):
            response = client.get("/health")

        payload = response.json()
        assert payload["status"] == "healthy"
        assert payload["dependencies"]["postgres"] == "healthy"
        assert payload["dependencies"]["redis"] == "healthy"

    def test_redis_connection_error_degrades_to_null(self, client: TestClient) -> None:
        """Test the realistic failure mode: Redis is unreachable."""
        import redis

        with patch.object(
            health_route,
            "get_safety_events_last_hour",
            side_effect=redis.ConnectionError("Error 111 connecting to localhost:6379"),
        ):
            response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["safety_events_last_hour"] is None

    def test_monitoring_failure_is_logged(self, client: TestClient) -> None:
        """Test the swallowed exception is still recorded for operators."""
        with (
            patch.object(
                health_route,
                "get_safety_events_last_hour",
                side_effect=Exception("monitoring unreachable"),
            ),
            patch.object(health_route, "log") as mock_log,
        ):
            client.get("/health")

        logged_events = [call[0][0] for call in mock_log.error.call_args_list]
        assert "safety_events_check_failed" in logged_events

    def test_field_present_when_a_dependency_is_down(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test the count still appears in the 503 detail payload."""

        class BrokenSession:
            async def execute(self, *args: Any, **kwargs: Any) -> None:
                raise Exception("postgres down")

        async def broken_get_db() -> AsyncGenerator[BrokenSession, None]:
            yield BrokenSession()

        app.dependency_overrides[get_db] = broken_get_db

        with patch.object(health_route, "get_safety_events_last_hour", return_value=7):
            response = client.get("/health")

        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["status"] == "unhealthy"
        assert detail["safety_events_last_hour"] == 7

    def test_no_live_redis_connection_is_opened(self, client: TestClient) -> None:
        """Test the count comes from the mocked function, not a real client."""
        with (
            patch.object(health_route, "get_safety_events_last_hour", return_value=5) as counter,
            patch("safety.monitoring._get_redis_client") as real_client,
        ):
            response = client.get("/health")

        assert response.json()["safety_events_last_hour"] == 5
        counter.assert_called_once_with()
        real_client.assert_not_called()
