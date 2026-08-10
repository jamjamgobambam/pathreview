"""Tests for api/routes/health.py"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.health import router
from core.database import get_db


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create a mock async DB session that succeeds by default."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)
        return db

    @pytest.fixture
    def app(self, mock_db: AsyncMock) -> FastAPI:
        """Create a FastAPI test app with health router and DB dependency overridden."""
        test_app = FastAPI()
        test_app.include_router(router)
        test_app.dependency_overrides[get_db] = lambda: mock_db
        return test_app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create a TestClient for the app."""
        return TestClient(app, raise_server_exceptions=False)

    def _mock_healthy_redis(self) -> Mock:
        """Build a mock redis.Redis instance that responds successfully to ping."""
        redis_instance = Mock()
        redis_instance.ping = Mock(return_value=True)
        return redis_instance

    def test_health_check_includes_safety_events_field(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that the response always includes safety_events_last_hour."""
        redis_instance = self._mock_healthy_redis()

        with (
            patch("redis.Redis", return_value=redis_instance),
            patch("core.config.settings") as mock_settings,
            patch("safety.monitoring.SafetyMonitor.get_total_event_count", return_value=3),
        ):
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://vector-db"

            response = client.get("/health")

        assert "safety_events_last_hour" in response.json()

    def test_health_check_reports_real_count_when_redis_healthy(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that safety_events_last_hour reflects a real queried value, not a stub."""
        redis_instance = self._mock_healthy_redis()

        with (
            patch("redis.Redis", return_value=redis_instance),
            patch("core.config.settings") as mock_settings,
            patch("safety.monitoring.SafetyMonitor.get_total_event_count", return_value=7),
        ):
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://vector-db"

            response = client.get("/health")

        data = response.json()
        assert data["safety_events_last_hour"] == 7
        assert data["dependencies"]["redis"] == "healthy"

    def test_health_check_returns_null_when_redis_unavailable(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that safety_events_last_hour is null (not 0) when Redis is down."""
        with (
            patch("redis.Redis", side_effect=Exception("Connection refused")),
            patch("core.config.settings") as mock_settings,
        ):
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://vector-db"

            response = client.get("/health")

        # Redis being down triggers a 503, with the health payload in `detail`
        assert response.status_code == 503
        data = response.json()["detail"]
        assert data["dependencies"]["redis"] == "unhealthy"
        assert data["safety_events_last_hour"] is None

    def test_health_check_does_not_query_safety_events_when_redis_down(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that SafetyMonitor isn't queried at all when Redis is unreachable."""
        with (
            patch("redis.Redis", side_effect=Exception("Connection refused")),
            patch("core.config.settings") as mock_settings,
            patch("safety.monitoring.SafetyMonitor.get_total_event_count") as mock_get_total,
        ):
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://vector-db"

            client.get("/health")

        mock_get_total.assert_not_called()

    def test_health_check_safety_events_failure_returns_null_not_crash(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that an exception inside the safety-events lookup doesn't break /health."""
        redis_instance = self._mock_healthy_redis()

        with (
            patch("redis.Redis", return_value=redis_instance),
            patch("core.config.settings") as mock_settings,
            patch(
                "safety.monitoring.SafetyMonitor.get_total_event_count",
                side_effect=Exception("boom"),
            ),
        ):
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://vector-db"

            response = client.get("/health")

        # Postgres and vector_db are still healthy, so overall status remains healthy
        data = response.json()
        assert response.status_code == 200
        assert data["safety_events_last_hour"] is None

    def test_health_check_returns_503_when_postgres_down(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that a Postgres failure still produces a 503 with full payload."""
        mock_db.execute = AsyncMock(side_effect=Exception("connection refused"))
        redis_instance = self._mock_healthy_redis()

        with (
            patch("redis.Redis", return_value=redis_instance),
            patch("core.config.settings") as mock_settings,
            patch("safety.monitoring.SafetyMonitor.get_total_event_count", return_value=0),
        ):
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://vector-db"

            response = client.get("/health")

        assert response.status_code == 503
        data = response.json()["detail"]
        assert data["dependencies"]["postgres"] == "unhealthy"
        assert data["status"] == "unhealthy"

    def test_health_check_returns_200_when_all_healthy(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test a fully healthy response returns 200 with status healthy."""
        redis_instance = self._mock_healthy_redis()

        with (
            patch("redis.Redis", return_value=redis_instance),
            patch("core.config.settings") as mock_settings,
            patch("safety.monitoring.SafetyMonitor.get_total_event_count", return_value=0),
        ):
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://vector-db"

            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["safety_events_last_hour"] == 0
