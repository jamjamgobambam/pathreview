"""Tests for RateLimitMiddleware header behavior."""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.rate_limit import RateLimitMiddleware


@pytest.fixture
def client() -> TestClient:
    """Build a minimal app with the rate limit middleware mounted."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(app)


@pytest.mark.unit
class TestRateLimitMiddlewareHeaders:
    """The middleware is where X-RateLimit-* headers are attached."""

    def test_allowed_response_includes_headers(self, client: TestClient) -> None:
        """A permitted request passes through and gets rate-limit headers."""
        with patch(
            "api.middleware.rate_limit.rate_limiter.check_rate_limit",
            return_value=(True, 7),
        ):
            response = client.get("/ping")

        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "60"
        assert response.headers["X-RateLimit-Remaining"] == "7"

    def test_denied_response_returns_429_with_headers(self, client: TestClient) -> None:
        """A blocked request returns 429 with rate-limit headers and no passthrough."""
        with patch(
            "api.middleware.rate_limit.rate_limiter.check_rate_limit",
            return_value=(False, 0),
        ):
            response = client.get("/ping")

        assert response.status_code == 429
        assert response.headers["X-RateLimit-Limit"] == "60"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.json() == {"detail": "Request limit exceeded"}
