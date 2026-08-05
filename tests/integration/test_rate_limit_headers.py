"""Integration tests for RateLimitMiddleware header behavior.

These tests exercise the middleware end-to-end via TestClient against a minimal
FastAPI app. The underlying RateLimiter's Redis interactions are already covered
in tests/unit/test_rate_limiter.py, so we inject a small in-memory stub with the
same (allowed, remaining) contract to keep these tests hermetic (no Redis, no
new deps).
"""

from collections import defaultdict

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from api.middleware.rate_limit import RateLimitMiddleware


class StubLimiter:
    """In-memory replacement for safety.rate_limiter.RateLimiter.

    Mirrors check_rate_limit()'s tuple contract but keeps counts in a dict so
    the rolling-window logic is deterministic in tests.
    """

    def __init__(self) -> None:
        self.counts: dict[str, int] = defaultdict(int)

    def check_rate_limit(
        self, identifier: str, limit: int, window_seconds: int = 60
    ) -> tuple[bool, int]:
        current = self.counts[identifier]
        if current < limit:
            self.counts[identifier] = current + 1
            return True, limit - current - 1
        return False, 0


def _build_client(limit: int = 60, window_seconds: int = 60) -> tuple[TestClient, StubLimiter]:
    """Build a minimal app with RateLimitMiddleware and one non-exempt route.

    /test is a normal route; /health is exempted by the middleware itself
    (EXEMPT_PATHS in api/middleware/rate_limit.py).
    """
    app = FastAPI()
    limiter = StubLimiter()
    app.add_middleware(
        RateLimitMiddleware,
        limiter=limiter,
        limit=limit,
        window_seconds=window_seconds,
    )

    @app.get("/test")
    def ok_route() -> dict:
        return {"status": "ok"}

    @app.get("/health")
    def health_route() -> dict:
        return {"status": "ok"}

    @app.get("/boom")
    def raising_route() -> dict:
        raise HTTPException(status_code=500, detail="boom")

    return TestClient(app), limiter


@pytest.mark.integration
class TestRateLimitHeaders:
    def test_headers_present_on_200_response(self) -> None:
        client, _ = _build_client(limit=60)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert resp.headers["X-RateLimit-Limit"] == "60"
        assert resp.headers["X-RateLimit-Remaining"] == "59"

    def test_remaining_decrements_across_calls(self) -> None:
        client, _ = _build_client(limit=60)
        r1 = client.get("/test")
        r2 = client.get("/test")
        r3 = client.get("/test")
        assert int(r1.headers["X-RateLimit-Remaining"]) == 59
        assert int(r2.headers["X-RateLimit-Remaining"]) == 58
        assert int(r3.headers["X-RateLimit-Remaining"]) == 57

    def test_returns_429_when_limit_exceeded(self) -> None:
        client, _ = _build_client(limit=3)
        # First 3 requests succeed and consume the budget
        for _ in range(3):
            assert client.get("/test").status_code == 200
        # 4th request is blocked
        blocked = client.get("/test")
        assert blocked.status_code == 429
        assert blocked.json() == {"detail": "Rate limit exceeded"}
        assert blocked.headers["X-RateLimit-Limit"] == "3"
        assert blocked.headers["X-RateLimit-Remaining"] == "0"
        assert blocked.headers["Retry-After"] == "60"

    def test_429_uses_configured_window_seconds_for_retry_after(self) -> None:
        client, _ = _build_client(limit=1, window_seconds=30)
        client.get("/test")  # burn the single allowed request
        blocked = client.get("/test")
        assert blocked.status_code == 429
        assert blocked.headers["Retry-After"] == "30"

    def test_exempt_path_has_no_ratelimit_headers(self) -> None:
        client, limiter = _build_client(limit=60)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" not in resp.headers
        assert "X-RateLimit-Remaining" not in resp.headers
        # And the exempt path must NOT consume budget
        assert not limiter.counts  # no identifiers tracked at all

    def test_exempt_root_path(self) -> None:
        client, limiter = _build_client(limit=60)

        # / is not defined on the test app but the middleware exempts it before
        # dispatching; register a route so the request has somewhere to land.
        @client.app.get("/")
        def root() -> dict:
            return {"root": True}

        resp = client.get("/")
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" not in resp.headers
        assert not limiter.counts

    def test_headers_present_on_error_response(self) -> None:
        """Headers must attach regardless of downstream status."""
        client, _ = _build_client(limit=60)
        resp = client.get("/boom")
        assert resp.status_code == 500
        assert resp.headers["X-RateLimit-Limit"] == "60"
        assert resp.headers["X-RateLimit-Remaining"] == "59"
