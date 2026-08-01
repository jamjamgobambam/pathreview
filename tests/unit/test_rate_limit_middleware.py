"""Tests for api/middleware/rate_limit.py"""

from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from api.middleware.rate_limit import RateLimitMiddleware
from core.security import create_access_token

LIMIT = 5


def build_app(
    redis_client: Mock,
    limit: int = LIMIT,
    trust_proxy: bool = False,
) -> FastAPI:
    """Create a minimal app with the rate limit middleware installed."""
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        redis_client=redis_client,
        limit=limit,
        trust_proxy=trust_proxy,
    )

    @app.get("/ping")
    def ping() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def zadd_keys(mock_redis: Mock) -> list[str]:
    """Return the Redis keys consumed via zadd, in call order."""
    return [call.args[0] for call in mock_redis.zadd.call_args_list]


@pytest.mark.unit
class TestRateLimitMiddleware:
    """Test suite for RateLimitMiddleware."""

    @pytest.fixture
    def mock_redis(self) -> Mock:
        """Create a mock Redis client with an empty rolling window."""
        mock = Mock()
        mock.zcard = Mock(return_value=0)
        return mock

    def test_request_under_limit_allowed(self, mock_redis: Mock) -> None:
        """A request under the IP budget passes through."""
        client = TestClient(build_app(mock_redis))
        response = client.get("/ping")
        assert response.status_code == 200
        assert zadd_keys(mock_redis) == ["rate_limit:ip:testclient"]

    def test_request_over_limit_rejected(self, mock_redis: Mock) -> None:
        """A request over the IP budget gets the full 429 contract."""
        mock_redis.zcard = Mock(return_value=LIMIT)
        client = TestClient(build_app(mock_redis))
        response = client.get("/ping")
        assert response.status_code == 429
        assert response.json() == {"detail": "Rate limit exceeded"}
        assert response.headers["Retry-After"] == "60"
        assert response.headers["X-RateLimit-Limit"] == str(LIMIT)
        assert response.headers["X-RateLimit-Remaining"] == "0"

    def test_health_exempt(self, mock_redis: Mock) -> None:
        """/health bypasses rate limiting entirely."""
        mock_redis.zcard = Mock(return_value=LIMIT)
        client = TestClient(build_app(mock_redis))
        response = client.get("/health")
        assert response.status_code == 200
        mock_redis.zcard.assert_not_called()

    def test_redis_error_fails_open(self, mock_redis: Mock) -> None:
        """Redis failures allow the request instead of blocking traffic."""
        mock_redis.zremrangebyscore = Mock(side_effect=ConnectionError("down"))
        client = TestClient(build_app(mock_redis))
        response = client.get("/ping")
        assert response.status_code == 200

    def test_redis_timeout_fails_open(self, mock_redis: Mock) -> None:
        """A Redis timeout allows the request instead of blocking traffic."""
        mock_redis.zremrangebyscore = Mock(side_effect=TimeoutError("timed out"))
        client = TestClient(build_app(mock_redis))
        response = client.get("/ping")
        assert response.status_code == 200

    def test_forwarded_header_ignored_by_default(self, mock_redis: Mock) -> None:
        """X-Forwarded-For is ignored unless proxy trust is enabled."""
        client = TestClient(build_app(mock_redis))
        client.get("/ping", headers={"X-Forwarded-For": "203.0.113.9"})
        assert zadd_keys(mock_redis) == ["rate_limit:ip:testclient"]

    def test_forwarded_header_used_when_trusted(self, mock_redis: Mock) -> None:
        """With trust_proxy, the first forwarded address is the identifier."""
        client = TestClient(build_app(mock_redis, trust_proxy=True))
        client.get("/ping", headers={"X-Forwarded-For": "203.0.113.9, 10.0.0.1"})
        assert zadd_keys(mock_redis) == ["rate_limit:ip:203.0.113.9"]

    def test_invalid_forwarded_header_falls_back(self, mock_redis: Mock) -> None:
        """An invalid forwarded value falls back to the direct peer address."""
        client = TestClient(build_app(mock_redis, trust_proxy=True))
        response = client.get("/ping", headers={"X-Forwarded-For": "not-an-ip"})
        assert response.status_code == 200
        assert zadd_keys(mock_redis) == ["rate_limit:ip:testclient"]

    def test_authenticated_request_consumes_both_budgets(self, mock_redis: Mock) -> None:
        """A valid Bearer token consumes the IP budget and the user budget."""
        token = create_access_token({"sub": "user-123"})
        client = TestClient(build_app(mock_redis))
        response = client.get("/ping", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert zadd_keys(mock_redis) == [
            "rate_limit:ip:testclient",
            "rate_limit:user:user-123",
        ]

    def test_user_budget_exceeded_rejected(self, mock_redis: Mock) -> None:
        """An authenticated request over the user budget gets a 429."""
        mock_redis.zcard = Mock(side_effect=[0, LIMIT])
        token = create_access_token({"sub": "user-123"})
        client = TestClient(build_app(mock_redis))
        response = client.get("/ping", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 429

    def test_malformed_token_treated_as_anonymous(self, mock_redis: Mock) -> None:
        """An undecodable Bearer token gets IP-only protection, not a 401."""
        client = TestClient(build_app(mock_redis))
        response = client.get("/ping", headers={"Authorization": "Bearer not-a-jwt"})
        assert response.status_code == 200
        assert zadd_keys(mock_redis) == ["rate_limit:ip:testclient"]

    def test_zero_limit_rejects_immediately(self, mock_redis: Mock) -> None:
        """A limit of zero rejects every request while Redis is available."""
        client = TestClient(build_app(mock_redis, limit=0))
        response = client.get("/ping")
        assert response.status_code == 429

    def test_missing_client_uses_unknown(self, mock_redis: Mock) -> None:
        """A request without a client address maps to the unknown identifier."""
        middleware = RateLimitMiddleware(FastAPI(), redis_client=mock_redis, limit=LIMIT)
        scope: dict[str, Any] = {
            "type": "http",
            "method": "GET",
            "path": "/ping",
            "headers": [],
            "query_string": b"",
        }
        assert middleware._client_ip(Request(scope)) == "unknown"
