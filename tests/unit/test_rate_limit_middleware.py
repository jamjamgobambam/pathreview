"""Tests for API rate-limit middleware."""

from unittest.mock import Mock, call

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse, Response

from api.middleware.rate_limit import RateLimitMiddleware
from api.middleware.request_id import RequestIDMiddleware
from safety.rate_limiter import RateLimiter


def create_test_app(
    limiter: Mock,
    *,
    limit: int = 3,
    outer_middleware: bool = False,
) -> tuple[FastAPI, dict[str, int]]:
    """Create a small application with rate limiting enabled."""
    app = FastAPI()
    route_calls = {"count": 0}

    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=limiter,
        limit=limit,
    )

    if outer_middleware:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173"],
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
        )
        app.add_middleware(RequestIDMiddleware)

    @app.get("/limited")
    async def limited_route() -> dict[str, str]:
        route_calls["count"] += 1
        return {"status": "ok"}

    @app.get("/teapot")
    async def teapot_route() -> None:
        raise HTTPException(status_code=418, detail="teapot")

    return app, route_calls


@pytest.mark.unit
class TestRateLimitMiddleware:
    """Test rate limiting at the HTTP boundary."""

    @pytest.fixture
    def limiter(self) -> Mock:
        """Create a mocked rate limiter."""
        return Mock(spec=RateLimiter)

    def test_allowed_response_includes_limit_headers(self, limiter: Mock) -> None:
        """An allowed request reports its configured and remaining quota."""
        limiter.check_rate_limit.return_value = (True, 2)
        app, _ = create_test_app(limiter)
        client = TestClient(app, client=("192.0.2.10", 50000))

        response = client.get("/limited")

        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "3"
        assert response.headers["X-RateLimit-Remaining"] == "2"
        limiter.check_rate_limit.assert_called_once_with("192.0.2.10", 3)

    def test_exhausted_client_receives_429_without_calling_route(self, limiter: Mock) -> None:
        """An exhausted client is rejected before route handling."""
        limiter.check_rate_limit.return_value = (False, 0)
        app, route_calls = create_test_app(limiter)

        response = TestClient(app).get("/limited")

        assert response.status_code == 429
        assert response.json() == {"detail": "Rate limit exceeded"}
        assert response.headers["X-RateLimit-Limit"] == "3"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert route_calls["count"] == 0

    def test_last_allowed_request_precedes_first_denied_request(self, limiter: Mock) -> None:
        """Remaining zero is allowed until the following request is denied."""
        limiter.check_rate_limit.side_effect = [(True, 0), (False, 0)]
        app, route_calls = create_test_app(limiter)
        client = TestClient(app)

        last_allowed = client.get("/limited")
        first_denied = client.get("/limited")

        assert last_allowed.status_code == 200
        assert last_allowed.headers["X-RateLimit-Remaining"] == "0"
        assert first_denied.status_code == 429
        assert first_denied.headers["X-RateLimit-Remaining"] == "0"
        assert route_calls["count"] == 1

    def test_different_client_ips_use_independent_identifiers(self, limiter: Mock) -> None:
        """Each client address is passed to the limiter separately."""
        limiter.check_rate_limit.return_value = (True, 2)
        app, _ = create_test_app(limiter)

        TestClient(app, client=("192.0.2.11", 50000)).get("/limited")
        TestClient(app, client=("192.0.2.12", 50000)).get("/limited")

        assert limiter.check_rate_limit.call_args_list == [
            call("192.0.2.11", 3),
            call("192.0.2.12", 3),
        ]

    def test_fail_open_result_preserves_service_and_full_quota(self, limiter: Mock) -> None:
        """The limiter's Redis fail-open result remains an allowed response."""
        limiter.check_rate_limit.return_value = (True, 3)
        app, route_calls = create_test_app(limiter)

        response = TestClient(app).get("/limited")

        assert response.status_code == 200
        assert response.headers["X-RateLimit-Remaining"] == "3"
        assert route_calls["count"] == 1

    @pytest.mark.asyncio
    async def test_missing_client_uses_stable_fallback_identifier(self, limiter: Mock) -> None:
        """A request without client metadata uses a stable fallback key."""
        limiter.check_rate_limit.return_value = (True, 2)
        middleware = RateLimitMiddleware(FastAPI(), rate_limiter=limiter, limit=3)
        request = Request(
            {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": "/limited",
                "raw_path": b"/limited",
                "query_string": b"",
                "headers": [],
                "client": None,
                "server": ("testserver", 80),
                "root_path": "",
            }
        )

        async def call_next(_request: Request) -> Response:
            return JSONResponse({"status": "ok"})

        response = await middleware.dispatch(request, call_next)

        assert response.headers["X-RateLimit-Remaining"] == "2"
        limiter.check_rate_limit.assert_called_once_with("unknown", 3)

    def test_route_generated_error_includes_limit_headers(self, limiter: Mock) -> None:
        """Handled application errors retain rate-limit metadata."""
        limiter.check_rate_limit.return_value = (True, 1)
        app, _ = create_test_app(limiter)

        response = TestClient(app).get("/teapot")

        assert response.status_code == 418
        assert response.headers["X-RateLimit-Limit"] == "3"
        assert response.headers["X-RateLimit-Remaining"] == "1"

    def test_rejected_response_retains_request_id_and_cors_headers(self, limiter: Mock) -> None:
        """Outer request-ID and CORS middleware process rejected responses."""
        limiter.check_rate_limit.return_value = (False, 0)
        app, _ = create_test_app(limiter, outer_middleware=True)

        response = TestClient(app).get(
            "/limited",
            headers={"Origin": "http://localhost:5173"},
        )

        exposed_headers = response.headers["Access-Control-Expose-Headers"]
        assert response.status_code == 429
        assert response.headers["X-Request-ID"]
        assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
        assert "X-RateLimit-Limit" in exposed_headers
        assert "X-RateLimit-Remaining" in exposed_headers
