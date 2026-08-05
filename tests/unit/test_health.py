import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import health as health_module
from core.database import get_db


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async DB session that succeeds by default."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings with a healthy redis host and vector db url."""
        settings = MagicMock()
        settings.redis_host = "localhost"
        settings.redis_port = 6379
        settings.vector_db_url = "http://vector-db:8000"
        return settings

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client whose ping() succeeds."""
        client = Mock()
        client.ping = Mock(return_value=True)
        return client

    @pytest.fixture
    def app(self, mock_db):
        """Create a FastAPI app with only the health router mounted."""
        app = FastAPI()
        app.include_router(health_module.router)

        async def _fake_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = _fake_get_db
        return app

    @pytest.fixture
    def client(self, app):
        """Create a TestClient for the health app."""
        return TestClient(app)

    def test_returns_200_when_all_dependencies_healthy(
        self, client, mock_settings, mock_redis_client
    ):
        """Test that a fully healthy system returns 200 with all deps healthy."""
        with patch("redis.Redis", return_value=mock_redis_client), \
             patch("core.config.settings", mock_settings), \
             patch.object(health_module, "SafetyMonitor") as mock_monitor_cls:

            mock_monitor_cls.return_value.get_total_event_count.return_value = 4

            response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["dependencies"]["postgres"] == "healthy"
        assert body["dependencies"]["redis"] == "healthy"
        assert body["dependencies"]["vector_db"] == "healthy"

    def test_safety_events_last_hour_comes_from_safety_monitor(
        self, client, mock_settings, mock_redis_client
    ):
        """Test that safety_events_last_hour reflects SafetyMonitor's total count."""
        with patch("redis.Redis", return_value=mock_redis_client), \
             patch("core.config.settings", mock_settings), \
             patch.object(health_module, "SafetyMonitor") as mock_monitor_cls:

            mock_monitor_cls.return_value.get_total_event_count.return_value = 7

            response = client.get("/health")

        assert response.json()["safety_events_last_hour"] == 7
        mock_monitor_cls.return_value.get_total_event_count.assert_called_once_with(
            window_hours=1
        )

    def test_safety_monitor_reuses_the_health_check_redis_client(
        self, client, mock_settings, mock_redis_client
    ):
        """Test that SafetyMonitor is built from the same client used to check Redis."""
        with patch("redis.Redis", return_value=mock_redis_client), \
             patch("core.config.settings", mock_settings), \
             patch.object(health_module, "SafetyMonitor") as mock_monitor_cls:

            mock_monitor_cls.return_value.get_total_event_count.return_value = 0

            client.get("/health")

        mock_monitor_cls.assert_called_once_with(mock_redis_client)

    def test_postgres_down_returns_503(self, app, client, mock_db, mock_settings, mock_redis_client):
        """Test that a Postgres failure returns a 503 with postgres marked unhealthy."""
        mock_db.execute.side_effect = Exception("connection refused")

        with patch("redis.Redis", return_value=mock_redis_client), \
             patch("core.config.settings", mock_settings), \
             patch.object(health_module, "SafetyMonitor") as mock_monitor_cls:

            mock_monitor_cls.return_value.get_total_event_count.return_value = 0

            response = client.get("/health")

        assert response.status_code == 503
        assert response.json()["detail"]["dependencies"]["postgres"] == "unhealthy"

    def test_redis_down_marks_unhealthy_and_safety_events_is_none(
        self, client, mock_settings
    ):
        """Test that a Redis outage returns null safety_events_last_hour, not 0."""
        with patch("redis.Redis", side_effect=ConnectionError("no redis")), \
             patch("core.config.settings", mock_settings), \
             patch.object(health_module, "SafetyMonitor") as mock_monitor_cls:

            response = client.get("/health")

        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["dependencies"]["redis"] == "unhealthy"
        assert detail["safety_events_last_hour"] is None
        mock_monitor_cls.assert_not_called()

    def test_vector_db_url_missing_is_unavailable_not_unhealthy(
        self, client, mock_redis_client
    ):
        """Test that a missing vector_db_url is reported as unavailable, not unhealthy."""
        settings = MagicMock()
        settings.redis_host = "localhost"
        settings.redis_port = 6379
        settings.vector_db_url = None

        with patch("redis.Redis", return_value=mock_redis_client), \
             patch("core.config.settings", settings), \
             patch.object(health_module, "SafetyMonitor") as mock_monitor_cls:

            mock_monitor_cls.return_value.get_total_event_count.return_value = 0

            response = client.get("/health")

        body = response.json()
        assert body["dependencies"]["vector_db"] == "unavailable"
        assert body["status"] == "healthy"

    def test_safety_monitor_error_falls_back_to_none_not_crash(
        self, client, mock_settings, mock_redis_client
    ):
        """Test that a SafetyMonitor failure degrades to null instead of a 500."""
        with patch("redis.Redis", return_value=mock_redis_client), \
             patch("core.config.settings", mock_settings), \
             patch.object(health_module, "SafetyMonitor") as mock_monitor_cls:

            mock_monitor_cls.return_value.get_total_event_count.side_effect = Exception("boom")

            response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["safety_events_last_hour"] is None
