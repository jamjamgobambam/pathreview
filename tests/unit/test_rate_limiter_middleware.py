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
    def client(self, mock_rate_limiter: MagicMock) -> TestClient:
        """Create a TestClient wrapping a minimal app with only the rate limiter middleware."""
        app = FastAPI()
        app.add_middleware(RateLimiterMiddleware, rate_limiter=mock_rate_limiter, limit=60)

        @app.get("/ping")
        def ping() -> dict[str, bool]:
            return {"ok": True}

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

    def test_malformed_jwt_not_rate_limited(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test a malformed/invalid JWT falls through unrestricted (no IP fallback yet)."""
        response = client.get("/ping", headers={"Authorization": "Bearer not.a.valid.jwt"})

        assert response.status_code == 200
        mock_rate_limiter.check_rate_limit.assert_not_called()

    def test_no_authorization_header_not_rate_limited(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test a request with no Authorization header falls through unrestricted."""
        response = client.get("/ping")

        assert response.status_code == 200
        mock_rate_limiter.check_rate_limit.assert_not_called()

    def test_non_bearer_scheme_not_rate_limited(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test an Authorization header using a non-Bearer scheme falls through unrestricted."""
        response = client.get("/ping", headers={"Authorization": "Basic dXNlcjpwYXNz"})

        assert response.status_code == 200
        mock_rate_limiter.check_rate_limit.assert_not_called()

    def test_authorization_header_without_bearer_prefix_not_rate_limited(
        self, client: TestClient, mock_rate_limiter: MagicMock
    ) -> None:
        """Test an Authorization header with no scheme prefix at all falls through unrestricted."""
        response = client.get("/ping", headers={"Authorization": "sometoken123"})

        assert response.status_code == 200
        mock_rate_limiter.check_rate_limit.assert_not_called()
