"""Tests for api/middleware/rate_limit.py"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.rate_limit import RateLimitMiddleware
from core.security import create_access_token
from safety.rate_limiter import RateLimiter


def _build_app() -> FastAPI:
    """Minimal app with only RateLimitMiddleware wired, to test it in isolation."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "ok"}

    return app


@pytest.mark.unit
class TestRateLimitMiddleware:
    """Test suite for RateLimitMiddleware."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a TestClient wrapping the minimal isolated app."""
        return TestClient(_build_app())

    def test_ip_over_limit_returns_429_without_calling_route(self, client: TestClient) -> None:
        """RateLimitMiddleware should short-circuit with 429 when the IP bucket is full."""
        with patch.object(RateLimiter, "check_rate_limit", return_value=(False, 0)):
            response = client.get("/")

        assert response.status_code == 429
        assert response.json()["detail"] == "Rate limit exceeded"

    def test_ip_allowed_no_auth_header_calls_route(self, client: TestClient) -> None:
        """With no Authorization header, only the IP layer is checked."""
        with patch.object(RateLimiter, "check_rate_limit", return_value=(True, 59)) as mock_check:
            response = client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "ok"}
        mock_check.assert_called_once()
        assert mock_check.call_args[0][0].startswith("ip:")

    def test_ip_allowed_user_over_limit_returns_429(self, client: TestClient) -> None:
        """IP passes but the authenticated user's own bucket is full."""
        token = create_access_token({"sub": "user-123"})

        with patch.object(RateLimiter, "check_rate_limit", side_effect=[(True, 59), (False, 0)]):
            response = client.get("/", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 429

    def test_ip_and_user_both_allowed_calls_route(self, client: TestClient) -> None:
        """Both layers allowed: the wrapped route actually runs."""
        token = create_access_token({"sub": "user-123"})

        with patch.object(
            RateLimiter, "check_rate_limit", side_effect=[(True, 59), (True, 59)]
        ) as mock_check:
            response = client.get("/", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert mock_check.call_count == 2
        first_key = mock_check.call_args_list[0][0][0]
        second_key = mock_check.call_args_list[1][0][0]
        assert first_key.startswith("ip:")
        assert second_key == "user:user-123"

    def test_invalid_token_falls_back_to_ip_only(self, client: TestClient) -> None:
        """A malformed/expired token is treated as anonymous, not an error."""
        with patch.object(RateLimiter, "check_rate_limit", return_value=(True, 59)) as mock_check:
            response = client.get("/", headers={"Authorization": "Bearer not-a-real-token"})

        assert response.status_code == 200
        mock_check.assert_called_once()
        assert mock_check.call_args[0][0].startswith("ip:")
