"""Tests for rate_limit.py"""

from unittest.mock import MagicMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import Response

from api.middleware.rate_limit import RateLimitMiddleware
from core.config import settings
from core.security import create_access_token


def make_request(
    headers: dict[str, str] | None = None, client_host: str | None = "1.2.3.4"
) -> Request:
    """Build a bare Starlette Request from a minimal ASGI scope."""
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": raw_headers,
        "client": (client_host, 12345) if client_host is not None else None,
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


@pytest.mark.unit
class TestRateLimitMiddleware:
    """Test suite for RateLimitMiddleware."""

    @pytest.fixture
    def mock_limiter(self) -> MagicMock:
        """Create a mock RateLimiter."""
        return MagicMock()

    @pytest.fixture
    def middleware(self, mock_limiter: MagicMock) -> RateLimitMiddleware:
        """Create a RateLimitMiddleware instance with a mocked RateLimiter."""
        with patch("api.middleware.rate_limit.redis.Redis.from_url"):
            mw = RateLimitMiddleware(app=MagicMock())
        mw.limiter = mock_limiter
        return mw

    # -- _resolve_identifier --

    def test_resolve_identifier_no_auth_header_falls_back_to_ip(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Test missing Authorization header falls back to client IP."""
        request = make_request(client_host="10.0.0.1")

        identifier = middleware._resolve_identifier(request)

        assert identifier == "10.0.0.1"

    def test_resolve_identifier_valid_bearer_token_returns_sub(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Test valid Bearer token with a sub claim returns that sub."""
        token = create_access_token(data={"sub": "user-123"})
        request = make_request(headers={"Authorization": f"Bearer {token}"})

        identifier = middleware._resolve_identifier(request)

        assert identifier == "user-123"

    def test_resolve_identifier_malformed_token_falls_back_to_ip(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Test undecodable token falls back to client IP."""
        request = make_request(
            headers={"Authorization": "Bearer not.a.valid.token"},
            client_host="10.0.0.2",
        )

        identifier = middleware._resolve_identifier(request)

        assert identifier == "10.0.0.2"

    def test_resolve_identifier_token_without_sub_falls_back_to_ip(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Test a token that decodes but has no sub claim falls back to client IP."""
        token = create_access_token(data={})
        request = make_request(
            headers={"Authorization": f"Bearer {token}"},
            client_host="10.0.0.3",
        )

        identifier = middleware._resolve_identifier(request)

        assert identifier == "10.0.0.3"

    def test_resolve_identifier_no_client_returns_unknown(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Test missing request.client with no valid token returns 'unknown'."""
        request = make_request(client_host=None)

        identifier = middleware._resolve_identifier(request)

        assert identifier == "unknown"

    # -- dispatch --

    @pytest.mark.asyncio
    async def test_dispatch_allowed_calls_call_next_and_attaches_headers(
        self, middleware: RateLimitMiddleware, mock_limiter: MagicMock
    ) -> None:
        """Test an allowed request runs call_next and attaches rate limit headers."""
        mock_limiter.check_rate_limit.return_value = (True, 42)
        request = make_request(client_host="10.0.0.4")

        async def call_next(_request: Request) -> Response:
            return Response("ok", status_code=200)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == str(settings.rate_limit_per_minute)
        assert response.headers["X-RateLimit-Remaining"] == "42"

    @pytest.mark.asyncio
    async def test_dispatch_denied_returns_429_without_calling_call_next(
        self, middleware: RateLimitMiddleware, mock_limiter: MagicMock
    ) -> None:
        """Test a denied request returns 429 with zero remaining, without running call_next."""
        mock_limiter.check_rate_limit.return_value = (False, 0)
        request = make_request(client_host="10.0.0.5")

        async def call_next(_request: Request) -> Response:
            raise AssertionError("call_next should not be called when rate limited")

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 429
        assert response.headers["X-RateLimit-Limit"] == str(settings.rate_limit_per_minute)
        assert response.headers["X-RateLimit-Remaining"] == "0"

    @pytest.mark.asyncio
    async def test_dispatch_calls_check_rate_limit_with_resolved_identifier_and_limit(
        self, middleware: RateLimitMiddleware, mock_limiter: MagicMock
    ) -> None:
        """Test dispatch passes the resolved identifier and configured limit to check_rate_limit."""
        mock_limiter.check_rate_limit.return_value = (True, 10)
        request = make_request(client_host="10.0.0.6")

        async def call_next(_request: Request) -> Response:
            return Response("ok", status_code=200)

        await middleware.dispatch(request, call_next)

        mock_limiter.check_rate_limit.assert_called_once_with(
            "10.0.0.6", settings.rate_limit_per_minute
        )
