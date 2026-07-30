"""Tests for api.middleware.rate_limit."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.rate_limit import RateLimitMiddleware


@pytest.mark.unit
class TestRateLimitMiddleware:
    """Test suite for RateLimitMiddleware."""

    @pytest.fixture
    def mock_limiter(self):
        """Create a mock RateLimiter."""
        limiter = MagicMock()
        limiter.check_rate_limit.return_value = (True, 59)
        return limiter

    @pytest.fixture
    def client(self, mock_limiter):
        """TestClient with controllable RateLimiter."""
        application = FastAPI()

        @application.get("/api/ping")
        async def ping():
            return {"ok": True}

        @application.get("/health")
        async def health():
            return {"status": "ok"}

        @application.get("/health/ready")
        async def health_ready():
            return {"ready": True}

        @application.get("/docs")
        async def docs():
            return {"docs": True}

        @application.get("/")
        async def root():
            return {"root": True}

        @application.options("/api/ping")
        async def ping_options():
            return {"ok": True}

        # Subclass so we can inject the mock limiter after construction
        class _ConfiguredRateLimitMiddleware(RateLimitMiddleware):
            def __init__(self, app):
                super().__init__(app, redis_client=MagicMock())
                self.limiter = mock_limiter
                self.limit = 60

        application.add_middleware(_ConfiguredRateLimitMiddleware)
        return TestClient(application), mock_limiter

    def test_allowed_request_calls_limiter_with_ip(self, client):
        """Allowed requests call the limiter with the client IP."""
        test_client, mock_limiter = client
        mock_limiter.check_rate_limit.return_value = (True, 59)

        response = test_client.get("/api/ping")

        assert response.status_code == 200
        mock_limiter.check_rate_limit.assert_called_once()
        kwargs = mock_limiter.check_rate_limit.call_args.kwargs
        assert "ip_address" in kwargs
        assert kwargs["ip_address"]  # non-empty
        assert kwargs["limit"] == 60

    def test_denied_returns_429(self, client):
        """Denied requests return HTTP 429 with a detail message."""
        test_client, mock_limiter = client
        mock_limiter.check_rate_limit.return_value = (False, 0)

        response = test_client.get("/api/ping")

        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    def test_missing_auth_passes_identifier_none(self, client):
        """Unauthenticated requests pass identifier=None."""
        test_client, mock_limiter = client
        mock_limiter.check_rate_limit.return_value = (True, 59)

        test_client.get("/api/ping")

        args = mock_limiter.check_rate_limit.call_args.args
        assert args[0] is None

    def test_valid_bearer_passes_sub(self, client):
        """Valid Bearer JWT passes the token sub as identifier."""
        test_client, mock_limiter = client
        mock_limiter.check_rate_limit.return_value = (True, 59)

        with patch(
            "api.middleware.rate_limit.decode_access_token",
            return_value={"sub": "user-abc"},
        ):
            test_client.get(
                "/api/ping",
                headers={"Authorization": "Bearer valid.token.here"},
            )

        args = mock_limiter.check_rate_limit.call_args.args
        assert args[0] == "user-abc"

    def test_invalid_bearer_treated_as_unauthenticated(self, client):
        """Invalid Bearer tokens are treated as unauthenticated."""
        test_client, mock_limiter = client
        mock_limiter.check_rate_limit.return_value = (True, 59)

        with patch(
            "api.middleware.rate_limit.decode_access_token",
            return_value=None,
        ):
            test_client.get(
                "/api/ping",
                headers={"Authorization": "Bearer bad.token"},
            )

        args = mock_limiter.check_rate_limit.call_args.args
        assert args[0] is None

    def test_exempt_health_does_not_call_limiter(self, client):
        """Health endpoints skip rate limiting."""
        test_client, mock_limiter = client

        response = test_client.get("/health")

        assert response.status_code == 200
        mock_limiter.check_rate_limit.assert_not_called()

    def test_exempt_health_subpath_does_not_call_limiter(self, client):
        """Health subpaths also skip rate limiting."""
        test_client, mock_limiter = client

        response = test_client.get("/health/ready")

        assert response.status_code == 200
        mock_limiter.check_rate_limit.assert_not_called()

    def test_exempt_docs_does_not_call_limiter(self, client):
        """OpenAPI docs skip rate limiting."""
        test_client, mock_limiter = client

        response = test_client.get("/docs")

        assert response.status_code == 200
        mock_limiter.check_rate_limit.assert_not_called()

    def test_exempt_root_does_not_call_limiter(self, client):
        """Root health-style path skips rate limiting."""
        test_client, mock_limiter = client

        response = test_client.get("/")

        assert response.status_code == 200
        mock_limiter.check_rate_limit.assert_not_called()

    def test_exempt_options_does_not_call_limiter(self, client):
        """CORS preflight OPTIONS requests skip rate limiting."""
        test_client, mock_limiter = client

        response = test_client.options("/api/ping")

        assert response.status_code == 200
        mock_limiter.check_rate_limit.assert_not_called()

    def test_is_exempt_helpers(self):
        """Exempt path helper matches expected prefixes."""
        assert RateLimitMiddleware._is_exempt("/") is True
        assert RateLimitMiddleware._is_exempt("/health") is True
        assert RateLimitMiddleware._is_exempt("/health/live") is True
        assert RateLimitMiddleware._is_exempt("/docs") is True
        assert RateLimitMiddleware._is_exempt("/openapi.json") is True
        assert RateLimitMiddleware._is_exempt("/redoc") is True
        assert RateLimitMiddleware._is_exempt("/api/ping") is False
        assert RateLimitMiddleware._is_exempt("/auth/login") is False
        # "/" is exact-only — other paths are still limited
        assert RateLimitMiddleware._is_exempt("/api") is False

    def test_client_ip_unknown_when_no_client(self):
        """Missing client peer falls back to 'unknown'."""
        request = MagicMock()
        request.client = None
        assert RateLimitMiddleware._client_ip(request) == "unknown"

    def test_client_ip_from_peer(self):
        """Client IP is taken from the connection peer host."""
        request = MagicMock()
        request.client.host = "203.0.113.10"
        assert RateLimitMiddleware._client_ip(request) == "203.0.113.10"
