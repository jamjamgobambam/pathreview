"""Tests for api/middleware/rate_limiter.py"""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.rate_limiter import RateLimiterMiddleware
from core.security import create_access_token


@pytest.mark.unit
class TestRateLimiterMiddleware:
    """Test suite for RateLimiterMiddleware.

    RateLimiter's own internal correctness (rolling window, per-identifier
    isolation, fail-open behavior) is covered by test_rate_limiter.py.
    This suite mocks RateLimiter directly and is scoped to the middleware's
    own responsibilities: token parsing, identifier extraction, and relaying
    check_rate_limit's output into response status/headers.
    """

    @pytest.fixture
    def mock_rate_limiter(self) -> MagicMock:
        """Create a mock RateLimiter."""
        return MagicMock()

    @pytest.fixture
    def app(self, mock_rate_limiter: MagicMock) -> FastAPI:
        """Create a minimal app with only the rate limiter middleware."""
        app = FastAPI()
        app.add_middleware(RateLimiterMiddleware, rate_limiter=mock_rate_limiter, limit=60)

        @app.get("/ping")
        def ping() -> dict[str, bool]:
            return {"ok": True}

        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create a TestClient wrapping the minimal app, using TestClient's default client host."""
        return TestClient(app)

    def test_valid_token_under_limit_allowed(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test valid JWT under the limit returns 200 with correct rate limit headers."""
        mock_rate_limiter.check_rate_limit.return_value = (True, 59)
        token = create_access_token({"sub": "user123"})

        response = client.get("/ping", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "60"
        assert response.headers["X-RateLimit-Remaining"] == "59"

    def test_remaining_decrements_across_requests(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test X-RateLimit-Remaining reflects each call's return value across repeated requests."""
        mock_rate_limiter.check_rate_limit.side_effect = [
            (True, 59),
            (True, 58),
            (True, 57),
        ]
        token = create_access_token({"sub": "user123"})

        remaining_values = []
        for _ in range(3):
            response = client.get("/ping", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            remaining_values.append(response.headers["X-RateLimit-Remaining"])

        assert remaining_values == ["59", "58", "57"]

    def test_valid_token_over_limit_denied(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test valid JWT at/over the limit returns 429 with X-RateLimit-Remaining: 0."""
        mock_rate_limiter.check_rate_limit.return_value = (False, 0)
        token = create_access_token({"sub": "user123"})

        response = client.get("/ping", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 429
        assert response.headers["X-RateLimit-Limit"] == "60"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.json() == {"detail": "Rate limit exceeded"}

    def test_different_users_use_distinct_identifiers(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test each user's JWT sub claim is passed as a distinct identifier to check_rate_limit."""
        mock_rate_limiter.check_rate_limit.return_value = (True, 59)
        token_a = create_access_token({"sub": "user_a"})
        token_b = create_access_token({"sub": "user_b"})

        client.get("/ping", headers={"Authorization": f"Bearer {token_a}"})
        client.get("/ping", headers={"Authorization": f"Bearer {token_b}"})

        identifiers = [
            call.kwargs["identifier"] for call in mock_rate_limiter.check_rate_limit.call_args_list
        ]
        assert identifiers == ["user_a", "user_b"]

    def test_malformed_jwt_falls_back_to_ip(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test a malformed/invalid JWT falls back to rate limiting by client IP."""
        mock_rate_limiter.check_rate_limit.return_value = (True, 59)

        response = client.get("/ping", headers={"Authorization": "Bearer not.a.valid.jwt"})

        assert response.status_code == 200
        mock_rate_limiter.check_rate_limit.assert_called_once_with(
            identifier="testclient", limit=60, window_seconds=60
        )

    def test_no_authorization_header_falls_back_to_ip(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test a request with no Authorization header falls back to rate limiting by client IP."""
        mock_rate_limiter.check_rate_limit.return_value = (True, 59)

        response = client.get("/ping")

        assert response.status_code == 200
        mock_rate_limiter.check_rate_limit.assert_called_once_with(
            identifier="testclient", limit=60, window_seconds=60
        )

    def test_non_bearer_scheme_falls_back_to_ip(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test a non-Bearer Authorization scheme falls back to IP-based rate limiting."""
        mock_rate_limiter.check_rate_limit.return_value = (True, 59)

        response = client.get("/ping", headers={"Authorization": "Basic dXNlcjpwYXNz"})

        assert response.status_code == 200
        mock_rate_limiter.check_rate_limit.assert_called_once_with(
            identifier="testclient", limit=60, window_seconds=60
        )

    def test_authorization_header_without_bearer_prefix_falls_back_to_ip(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test an Authorization header with no scheme prefix falls back to rate limiting by IP."""
        mock_rate_limiter.check_rate_limit.return_value = (True, 59)

        response = client.get("/ping", headers={"Authorization": "sometoken123"})

        assert response.status_code == 200
        mock_rate_limiter.check_rate_limit.assert_called_once_with(
            identifier="testclient", limit=60, window_seconds=60
        )

    def test_ip_fallback_denies_over_limit(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test an unauthenticated request over the limit is denied same as the JWT path."""
        mock_rate_limiter.check_rate_limit.return_value = (False, 0)

        response = client.get("/ping")

        assert response.status_code == 429
        assert response.headers["X-RateLimit-Remaining"] == "0"

    def test_different_client_ips_use_distinct_identifiers(
        self, app: FastAPI, mock_rate_limiter: MagicMock
    ) -> None:
        """Test unauthenticated requests from different IPs are isolated, like the JWT case."""
        mock_rate_limiter.check_rate_limit.return_value = (True, 59)
        client_a = TestClient(app, client=("1.2.3.4", 12345))
        client_b = TestClient(app, client=("5.6.7.8", 54321))

        client_a.get("/ping")
        client_b.get("/ping")

        identifiers = [
            call.kwargs["identifier"] for call in mock_rate_limiter.check_rate_limit.call_args_list
        ]
        assert identifiers == ["1.2.3.4", "5.6.7.8"]

    def test_valid_jwt_takes_priority_over_ip(
        self, app: FastAPI, mock_rate_limiter: MagicMock
    ) -> None:
        """Test a valid JWT's sub claim is used over client IP when both are available."""
        mock_rate_limiter.check_rate_limit.return_value = (True, 59)
        token = create_access_token({"sub": "user123"})
        client = TestClient(app, client=("9.9.9.9", 12345))

        client.get("/ping", headers={"Authorization": f"Bearer {token}"})

        mock_rate_limiter.check_rate_limit.assert_called_once_with(
            identifier="user123", limit=60, window_seconds=60
        )
