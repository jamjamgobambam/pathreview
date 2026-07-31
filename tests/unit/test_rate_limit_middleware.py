"""Tests for api/middleware/rate_limit.py"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from api.middleware.rate_limit import RateLimitMiddleware, _identify_request
from core.security import create_access_token


def _fake_request(headers: dict[str, str] | None = None, ip: str = "1.2.3.4"):
    return SimpleNamespace(
        headers=headers or {},
        client=SimpleNamespace(host=ip),
        url=SimpleNamespace(path="/"),
    )


@pytest.mark.unit
class TestIdentifyRequest:
    """Test suite for _identify_request."""

    def test_no_auth_header_uses_ip(self):
        request = _fake_request(ip="10.0.0.1")

        identifier = _identify_request(request)

        assert identifier == "ip:10.0.0.1"

    def test_no_client_falls_back_to_unknown(self):
        request = _fake_request()
        request.client = None

        identifier = _identify_request(request)

        assert identifier == "ip:unknown"

    def test_invalid_bearer_token_falls_back_to_ip(self):
        request = _fake_request(headers={"Authorization": "Bearer not-a-real-token"}, ip="10.0.0.2")

        identifier = _identify_request(request)

        assert identifier == "ip:10.0.0.2"

    def test_valid_bearer_token_uses_user_id(self):
        token = create_access_token(data={"sub": "user-123"})
        request = _fake_request(headers={"Authorization": f"Bearer {token}"})

        identifier = _identify_request(request)

        assert identifier == "user:user-123"

    def test_non_bearer_auth_header_falls_back_to_ip(self):
        request = _fake_request(headers={"Authorization": "Basic dXNlcjpwYXNz"}, ip="10.0.0.3")

        identifier = _identify_request(request)

        assert identifier == "ip:10.0.0.3"


def _build_app():
    async def homepage(request):
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/", homepage), Route("/health", homepage)])
    app.add_middleware(RateLimitMiddleware)
    return app


@pytest.mark.unit
class TestRateLimitMiddlewareDispatch:
    """Test suite for RateLimitMiddleware.dispatch."""

    def test_allowed_request_gets_headers_and_response(self):
        with patch("api.middleware.rate_limit.RateLimiter") as mock_limiter_cls:
            mock_limiter_cls.return_value.check_rate_limit.return_value = (True, 42)
            client = TestClient(_build_app())

            response = client.get("/")

        assert response.status_code == 200
        assert response.text == "ok"
        assert response.headers["X-RateLimit-Limit"] == "60"
        assert response.headers["X-RateLimit-Remaining"] == "42"

    def test_denied_request_returns_429_with_headers(self):
        with patch("api.middleware.rate_limit.RateLimiter") as mock_limiter_cls:
            mock_limiter_cls.return_value.check_rate_limit.return_value = (False, 0)
            client = TestClient(_build_app())

            response = client.get("/")

        assert response.status_code == 429
        assert response.headers["X-RateLimit-Limit"] == "60"
        assert response.headers["X-RateLimit-Remaining"] == "0"

    def test_excluded_path_skips_rate_limiting(self):
        with patch("api.middleware.rate_limit.RateLimiter") as mock_limiter_cls:
            mock_limiter_cls.return_value.check_rate_limit.return_value = (False, 0)
            client = TestClient(_build_app())

            response = client.get("/health")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers
        mock_limiter_cls.return_value.check_rate_limit.assert_not_called()
