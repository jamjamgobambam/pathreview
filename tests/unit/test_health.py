from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.database import get_db


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async DB session that succeeds by default."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)
        return db

    @pytest.fixture
    def client(self, mock_db):
        """TestClient with the get_db dependency overridden."""

        async def _override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = _override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_redis_healthy_when_reachable(self, client) -> None:
        """Redis check should report healthy when redis.from_url + ping succeed."""
        mock_redis_client = Mock()
        mock_redis_client.ping = Mock(return_value=True)

        with patch("redis.from_url", return_value=mock_redis_client) as mock_from_url:
            response = client.get("/health")

        body = response.json()
        payload = body.get("detail", body)

        assert payload["dependencies"]["redis"] == "healthy"
        mock_from_url.assert_called_once()

    def test_redis_unhealthy_when_connection_fails(self, client) -> None:
        """Redis check should report unhealthy (not crash) when the connection fails."""
        with patch("redis.from_url", side_effect=Exception("Connection refused")):
            response = client.get("/health")

        assert response.status_code == 503
        body = response.json()["detail"]
        assert body["dependencies"]["redis"] == "unhealthy"
        assert body["status"] == "unhealthy"

    def test_redis_check_uses_redis_url_not_undefined_fields(self, client) -> None:
        """
        Regression test for #155: the health check must use settings.redis_url,
        not settings.redis_host / settings.redis_port, which don't exist on Settings.
        """
        mock_redis_client = Mock()
        mock_redis_client.ping = Mock(return_value=True)

        with patch("redis.from_url", return_value=mock_redis_client) as mock_from_url:
            response = client.get("/health")

        args, kwargs = mock_from_url.call_args
        assert len(args) >= 1
        assert "host" not in kwargs
        assert "port" not in kwargs

        body = response.json().get("detail", response.json())
        assert body["dependencies"]["redis"] == "healthy"

    def test_postgres_healthy_when_db_succeeds(self, client, mock_db) -> None:
        """Postgres check should report healthy when the DB query succeeds."""
        with patch("redis.from_url") as mock_from_url:
            mock_from_url.return_value.ping = Mock(return_value=True)
            response = client.get("/health")

        body = response.json().get("detail", response.json())
        assert body["dependencies"]["postgres"] == "healthy"

    def test_postgres_unhealthy_when_db_fails(self, client, mock_db) -> None:
        """Postgres check should report unhealthy when the DB query raises."""
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection failed"))

        with patch("redis.from_url") as mock_from_url:
            mock_from_url.return_value.ping = Mock(return_value=True)
            response = client.get("/health")

        assert response.status_code == 503
        body = response.json()["detail"]
        assert body["dependencies"]["postgres"] == "unhealthy"

    def test_response_includes_all_dependency_keys(self, client) -> None:
        """Response should always report postgres, redis, and vector_db keys."""
        with patch("redis.from_url") as mock_from_url:
            mock_from_url.return_value.ping = Mock(return_value=True)
            response = client.get("/health")

        body = response.json().get("detail", response.json())
        assert set(body["dependencies"].keys()) == {"postgres", "redis", "vector_db"}

    def test_all_healthy_returns_200(self, client):
        """When every dependency is healthy, the endpoint should return 200."""
        with patch("redis.from_url") as mock_from_url:
            mock_from_url.return_value.ping = Mock(return_value=True)
            response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
