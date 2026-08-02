"""Tests for api/middleware/rate_limit.py"""

from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.rate_limit import RateLimitMiddleware
from core.security import create_access_token


def build_app(
    rate_limiter: Mock,
    ip_limit: int = 5,
    user_limit: int = 5,
    window_seconds: int = 60,
    exclude_paths: frozenset[str] = frozenset({"/health"}),
) -> FastAPI:
    app = FastAPI()

    @app.get("/public")
    async def public() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/health")
    async def health() -> dict[str, bool]:
        return {"ok": True}

    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=rate_limiter,
        ip_limit=ip_limit,
        user_limit=user_limit,
        window_seconds=window_seconds,
        exclude_paths=exclude_paths,
    )
    return app


@pytest.mark.unit
class TestRateLimitMiddleware:
    """Test suite for RateLimitMiddleware."""

    def test_unauthenticated_request_checked_against_ip_limit(self) -> None:
        """Unauthenticated requests should still be rate limited, by IP."""
        rate_limiter = Mock()
        rate_limiter.check_rate_limit.return_value = (True, 4)

        client = TestClient(build_app(rate_limiter))
        response = client.get("/public")

        assert response.status_code == 200
        rate_limiter.check_rate_limit.assert_called_once()
        call_args = rate_limiter.check_rate_limit.call_args
        assert call_args[0][0].startswith("ip:")

    def test_unauthenticated_request_blocked_when_ip_limit_exceeded(self) -> None:
        """Unauthenticated requests over the IP limit get a 429."""
        rate_limiter = Mock()
        rate_limiter.check_rate_limit.return_value = (False, 0)

        client = TestClient(build_app(rate_limiter))
        response = client.get("/public")

        assert response.status_code == 429
        assert "Retry-After" in response.headers

    def test_authenticated_request_checked_against_both_limits(self) -> None:
        """Authenticated requests should be checked by IP and by user."""
        rate_limiter = Mock()
        rate_limiter.check_rate_limit.return_value = (True, 4)
        token = create_access_token({"sub": "user-123"})

        client = TestClient(build_app(rate_limiter))
        response = client.get("/public", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        identifiers = [c[0][0] for c in rate_limiter.check_rate_limit.call_args_list]
        assert "ip:testclient" in identifiers
        assert "user:user-123" in identifiers

    def test_authenticated_request_blocked_when_user_limit_exceeded(self) -> None:
        """A user over their own limit is blocked even if the IP limit is fine."""
        rate_limiter = Mock()
        rate_limiter.check_rate_limit.side_effect = [(True, 4), (False, 0)]
        token = create_access_token({"sub": "user-123"})

        client = TestClient(build_app(rate_limiter))
        response = client.get("/public", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 429

    def test_invalid_token_falls_back_to_ip_only(self) -> None:
        """A malformed/invalid bearer token shouldn't error, just skip the user check."""
        rate_limiter = Mock()
        rate_limiter.check_rate_limit.return_value = (True, 4)

        client = TestClient(build_app(rate_limiter))
        response = client.get("/public", headers={"Authorization": "Bearer not-a-real-token"})

        assert response.status_code == 200
        rate_limiter.check_rate_limit.assert_called_once()

    def test_excluded_path_skips_rate_limiting(self) -> None:
        """Excluded paths (like health checks) should bypass rate limiting entirely."""
        rate_limiter = Mock()

        client = TestClient(build_app(rate_limiter))
        response = client.get("/health")

        assert response.status_code == 200
        rate_limiter.check_rate_limit.assert_not_called()
