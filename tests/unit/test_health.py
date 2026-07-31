"""Tests for api/routes/health.py"""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.health import router as health_router
from core.database import get_db


@pytest.fixture
def client() -> TestClient:
    """TestClient for a minimal app with only the health router mounted.

    Avoids importing api.main (and therefore auth/profiles/reviews and their
    service-layer dependencies), which aren't relevant to this endpoint.
    """

    async def override_get_db() -> AsyncIterator[Any]:
        yield AsyncMock()

    app = FastAPI()
    app.include_router(health_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint's Redis probe."""

    def test_redis_healthy_reports_healthy(self, client: TestClient) -> None:
        """When Redis responds to ping(), the endpoint should report it as healthy."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True

        with patch("redis.Redis.from_url", return_value=mock_redis) as mock_from_url:
            response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["dependencies"]["redis"] == "healthy"
        # Confirms the fix: connects via the existing redis_url setting, not
        # nonexistent redis_host/redis_port attributes.
        mock_from_url.assert_called_once()
        called_url = mock_from_url.call_args.args[0]
        assert called_url.startswith("redis://")

    def test_redis_unreachable_reports_unhealthy_without_crashing(self, client: TestClient) -> None:
        """A connection failure should be caught and reported, not raised as a 500."""
        with patch(
            "redis.Redis.from_url",
            side_effect=ConnectionError("Connection refused"),
        ):
            response = client.get("/health")

        assert response.status_code == 503
        body = response.json()["detail"]
        assert body["dependencies"]["redis"] == "unhealthy"
        # Postgres check (mocked healthy) shouldn't be affected by the Redis failure.
        assert body["dependencies"]["postgres"] == "healthy"

    def test_malformed_redis_url_handled_gracefully(self, client: TestClient) -> None:
        """A malformed REDIS_URL should degrade to 'unhealthy', not an unhandled 500."""
        with patch("redis.Redis.from_url", side_effect=ValueError("Invalid Redis URL")):
            response = client.get("/health")

        assert response.status_code == 503
        assert response.json()["detail"]["dependencies"]["redis"] == "unhealthy"

    def test_settings_has_no_removed_redis_host_attribute(self) -> None:
        """Regression guard: the fix must not depend on fields that don't exist on Settings."""
        from core.config import settings

        assert not hasattr(settings, "redis_host")
        assert not hasattr(settings, "redis_port")
        assert hasattr(settings, "redis_url")
