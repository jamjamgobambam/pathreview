"""Tests for api/middleware/rate_limit.py"""

from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.rate_limit import RateLimitMiddleware


def build_app(mock_redis: Mock) -> FastAPI:
    """Build a minimal FastAPI app with the rate limit middleware attached."""
    app = FastAPI()

    @app.get("/ping")
    async def ping():
        return {"pong": True}

    app.add_middleware(RateLimitMiddleware, redis_client=mock_redis)
    return app


@pytest.mark.unit
class TestRateLimitMiddleware:
    """Test suite for RateLimitMiddleware."""

    @pytest.fixture
    def mock_redis(self):
        redis_client = Mock()
        redis_client.zremrangebyscore = Mock()
        redis_client.zcard = Mock(return_value=0)
        redis_client.zadd = Mock()
        redis_client.expire = Mock()
        return redis_client

    def test_headers_present_on_success(self, mock_redis):
        client = TestClient(build_app(mock_redis))

        response = client.get("/ping")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_remaining_reflects_limiter_output(self, mock_redis):
        mock_redis.zcard = Mock(return_value=5)
        client = TestClient(build_app(mock_redis))

        response = client.get("/ping")

        limit = int(response.headers["X-RateLimit-Limit"])
        remaining = int(response.headers["X-RateLimit-Remaining"])
        assert remaining == limit - 5 - 1

    def test_blocked_request_returns_429_with_headers(self, mock_redis):
        mock_redis.zcard = Mock(return_value=10_000)
        client = TestClient(build_app(mock_redis))

        response = client.get("/ping")

        assert response.status_code == 429
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert "X-RateLimit-Limit" in response.headers

    def test_remaining_never_negative(self, mock_redis):
        mock_redis.zcard = Mock(return_value=10_000)
        client = TestClient(build_app(mock_redis))

        response = client.get("/ping")

        assert int(response.headers["X-RateLimit-Remaining"]) >= 0
