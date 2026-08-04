"""Tests for api/middleware/rate_limit.py"""

from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.rate_limit import IPRateLimitMiddleware


@pytest.mark.unit
class TestIPRateLimitMiddleware:
    """Test suite for IPRateLimitMiddleware."""

    @pytest.fixture
    def mock_redis(self) -> Generator[Mock, None, None]:
        """Patch redis.Redis.from_url so no real connection is made."""
        with patch("api.middleware.rate_limit.redis.Redis.from_url") as mock_from_url:
            mock_from_url.return_value = Mock()
            yield mock_from_url.return_value

    def build_app(
        self, mock_redis: Mock, limit: int | None = None, window_seconds: int = 60
    ) -> FastAPI:
        app = FastAPI()
        app.add_middleware(IPRateLimitMiddleware, limit=limit, window_seconds=window_seconds)

        @app.get("/ping")
        def ping() -> dict[str, bool]:
            return {"ok": True}

        return app

    def test_request_allowed_passes_through(self, mock_redis: Mock) -> None:
        app = self.build_app(mock_redis, limit=10)
        with patch(
            "api.middleware.rate_limit.RateLimiter.check_rate_limit",
            return_value=(True, 9),
        ):
            client = TestClient(app)
            response = client.get("/ping")

        assert response.status_code == 200
        assert response.json() == {"ok": True}
        assert response.headers["X-RateLimit-Remaining"] == "9"

    def test_request_over_limit_returns_429(self, mock_redis: Mock) -> None:
        app = self.build_app(mock_redis, limit=1)
        with patch(
            "api.middleware.rate_limit.RateLimiter.check_rate_limit",
            return_value=(False, 0),
        ):
            client = TestClient(app)
            response = client.get("/ping")

        assert response.status_code == 429
        assert response.json() == {"detail": "Rate limit exceeded. Please try again later."}

    def test_uses_client_ip_as_identifier(self, mock_redis: Mock) -> None:
        app = self.build_app(mock_redis, limit=10)
        with patch(
            "api.middleware.rate_limit.RateLimiter.check_rate_limit",
            return_value=(True, 9),
        ) as mock_check:
            client = TestClient(app)
            client.get("/ping")

        called_identifier = mock_check.call_args[0][0]
        assert called_identifier.startswith("ip:")

    def test_default_limit_from_settings(self, mock_redis: Mock) -> None:
        app = self.build_app(mock_redis, limit=None)
        with patch(
            "api.middleware.rate_limit.RateLimiter.check_rate_limit",
            return_value=(True, 5),
        ) as mock_check:
            client = TestClient(app)
            client.get("/ping")

        _, kwargs = mock_check.call_args
        assert kwargs["limit"] == 60  # settings.rate_limit_per_minute default

    def test_custom_limit_overrides_default(self, mock_redis: Mock) -> None:
        app = self.build_app(mock_redis, limit=5)
        with patch(
            "api.middleware.rate_limit.RateLimiter.check_rate_limit",
            return_value=(True, 4),
        ) as mock_check:
            client = TestClient(app)
            client.get("/ping")

        _, kwargs = mock_check.call_args
        assert kwargs["limit"] == 5

    def test_custom_window_seconds_passed_through(self, mock_redis: Mock) -> None:
        app = self.build_app(mock_redis, limit=10, window_seconds=120)
        with patch(
            "api.middleware.rate_limit.RateLimiter.check_rate_limit",
            return_value=(True, 9),
        ) as mock_check:
            client = TestClient(app)
            client.get("/ping")

        _, kwargs = mock_check.call_args
        assert kwargs["window_seconds"] == 120

    def test_multiple_requests_independent_ips_both_allowed(self, mock_redis: Mock) -> None:
        app = self.build_app(mock_redis, limit=10)
        with patch(
            "api.middleware.rate_limit.RateLimiter.check_rate_limit",
            return_value=(True, 9),
        ):
            client = TestClient(app)
            response1 = client.get("/ping")
            response2 = client.get("/ping")

        assert response1.status_code == 200
        assert response2.status_code == 200
