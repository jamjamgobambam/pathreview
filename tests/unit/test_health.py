"""Tests for api/routes/health.py"""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import health
from core.database import get_db
from core.redis import get_redis


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint."""

    @pytest.fixture
    def mock_db(self) -> Mock:
        """Create a mock DB session whose execute() succeeds."""
        db = Mock()
        db.execute = AsyncMock(return_value=None)
        return db

    @pytest.fixture
    def mock_redis(self) -> Mock:
        """Create a mock Redis client that behaves as healthy with no events."""
        redis_client = Mock()
        redis_client.ping = Mock(return_value=True)
        redis_client.zremrangebyscore = Mock()
        redis_client.zcount = Mock(return_value=0)
        return redis_client

    @pytest.fixture
    def client(self, mock_db: Mock, mock_redis: Mock) -> TestClient:
        """Create a TestClient with DB/Redis dependencies overridden."""
        app = FastAPI()
        app.include_router(health.router)
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_redis] = lambda: mock_redis
        return TestClient(app)

    def test_health_ok_includes_safety_events_field(self, client: TestClient) -> None:
        """Test the response includes safety_events_last_hour when all deps are up."""
        response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert "safety_events_last_hour" in body
        assert body["safety_events_last_hour"] == 0

    def test_health_reflects_logged_safety_events(
        self, client: TestClient, mock_redis: Mock
    ) -> None:
        """Test safety_events_last_hour sums counts across event types."""
        counts_by_key = {
            "safety:events:pii_detected": 3,
            "safety:events:injection_attempt": 2,
            "safety:events:content_filtered": 0,
            "safety:events:bias_detected": 0,
            "safety:events:rate_limited": 1,
        }
        mock_redis.zcount = Mock(side_effect=lambda key, *_args: counts_by_key[key])

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["safety_events_last_hour"] == 6

    def test_health_safety_query_failure_defaults_to_zero(
        self, client: TestClient, mock_redis: Mock
    ) -> None:
        """Test a Redis failure during the safety count degrades to 0, not a 500."""
        mock_redis.zremrangebyscore = Mock(side_effect=Exception("Redis error"))

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["safety_events_last_hour"] == 0

    def test_health_redis_down_returns_503(self, client: TestClient, mock_redis: Mock) -> None:
        """Test overall status is unhealthy (503) when Redis is down."""
        mock_redis.ping = Mock(side_effect=Exception("connection refused"))

        response = client.get("/health")

        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["dependencies"]["redis"] == "unhealthy"
        assert detail["status"] == "unhealthy"

    def test_health_postgres_down_returns_503(self, client: TestClient, mock_db: Mock) -> None:
        """Test overall status is unhealthy (503) when Postgres is down."""
        mock_db.execute = AsyncMock(side_effect=Exception("connection refused"))

        response = client.get("/health")

        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["dependencies"]["postgres"] == "unhealthy"
