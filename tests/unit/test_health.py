"""Tests for health.py"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.mark.unit
class TestHealthCheck:
    """Tests for the /health endpoint's dependency checks."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a TestClient instance for the app."""
        return TestClient(app)

    @patch("redis.from_url")
    def test_redis_healthy_when_reachable(
        self, mock_from_url: MagicMock, client: TestClient
    ) -> None:
        """Test /health reports redis as healthy when ping succeeds."""
        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_from_url.return_value = mock_redis_client

        response = client.get("/health")
        body = response.json().get("detail", response.json())

        assert body["dependencies"]["redis"] == "healthy"
        mock_from_url.assert_called_once()

    @patch("redis.from_url")
    def test_redis_unhealthy_when_unreachable(
        self, mock_from_url: MagicMock, client: TestClient
    ) -> None:
        """Test /health reports redis as unhealthy without raising an unhandled error."""
        mock_redis_client = MagicMock()
        mock_redis_client.ping.side_effect = ConnectionError("Connection refused")
        mock_from_url.return_value = mock_redis_client

        response = client.get("/health")
        body = response.json().get("detail", response.json())

        assert body["dependencies"]["redis"] == "unhealthy"

    def test_redis_check_uses_redis_url_not_missing_attribute(self, client: TestClient) -> None:
        """Regression test for #155: health check must not reference a
        nonexistent Settings attribute (redis_host/redis_port)."""
        response = client.get("/health")

        assert response.status_code != 500

    @patch("redis.from_url")
    def test_redis_from_url_called_with_settings_redis_url(
        self, mock_from_url: MagicMock, client: TestClient
    ) -> None:
        """Test the redis client is built from settings.redis_url."""
        from core.config import settings

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_from_url.return_value = mock_redis_client

        client.get("/health")

        mock_from_url.assert_called_once_with(settings.redis_url, decode_responses=True)
