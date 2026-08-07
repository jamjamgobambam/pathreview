"""Tests for api/routes/health.py"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import redis
from fastapi.testclient import TestClient

from api.main import app
from core.config import settings
from core.database import get_db


@pytest.fixture
def client():
    """Create a TestClient with the database dependency stubbed out.

    The stub keeps the Postgres probe healthy so that each assertion isolates
    the behavior of the Redis probe.
    """
    mock_session = Mock()
    mock_session.execute = AsyncMock(return_value=None)
    app.dependency_overrides[get_db] = lambda: mock_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.unit
class TestHealthCheckRedis:
    """Test suite for the Redis probe in the /health endpoint."""

    def test_reachable_redis_reports_healthy(self, client):
        """Test a responding Redis is reported as healthy."""
        with patch("redis.Redis.from_url") as mock_from_url:
            mock_from_url.return_value.ping.return_value = True
            response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["dependencies"]["redis"] == "healthy"

    def test_unreachable_redis_reports_unhealthy(self, client):
        """Test a refused Redis connection is reported as unhealthy."""
        with patch("redis.Redis.from_url") as mock_from_url:
            mock_from_url.return_value.ping.side_effect = redis.ConnectionError(
                "Connection refused"
            )
            response = client.get("/health")

        assert response.status_code == 503
        assert response.json()["detail"]["dependencies"]["redis"] == "unhealthy"

    def test_client_is_built_from_redis_url(self, client):
        """Test the Redis client is constructed from the redis_url setting.

        Regression guard for issue #155: the probe previously read
        settings.redis_host and settings.redis_port, which do not exist on
        Settings, so it raised AttributeError instead of connecting.
        """
        with patch("redis.Redis.from_url") as mock_from_url:
            mock_from_url.return_value.ping.return_value = True
            client.get("/health")

        mock_from_url.assert_called_once()
        assert mock_from_url.call_args.args[0] == settings.redis_url
        assert mock_from_url.call_args.kwargs["decode_responses"] is True

    def test_settings_exposes_redis_url_only(self):
        """Test Settings defines redis_url and not redis_host or redis_port."""
        assert settings.redis_url
        assert not hasattr(settings, "redis_host")
        assert not hasattr(settings, "redis_port")


@pytest.mark.unit
class TestHealthCheckRedisUrlHandling:
    """Test suite for how the Redis probe handles bad redis_url values.

    These exercise the real redis.Redis.from_url parser rather than a mock,
    which is safe because it rejects an invalid URL before opening a socket.
    """

    @pytest.mark.parametrize(
        "bad_url",
        ["", "not-a-url", "http://localhost:6379"],
        ids=["empty", "no_scheme", "wrong_scheme"],
    )
    def test_invalid_redis_url_reports_unhealthy(self, client, monkeypatch, bad_url):
        """Test an unparseable redis_url is reported without crashing the endpoint."""
        monkeypatch.setattr(settings, "redis_url", bad_url)

        response = client.get("/health")

        assert response.status_code == 503
        assert response.json()["detail"]["dependencies"]["redis"] == "unhealthy"
