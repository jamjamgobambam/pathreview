"""Unit tests for RateLimitMiddleware.

These isolate the middleware's per-method behavior with a stateless in-memory
`StubLimiter` and a synthesized `SimpleNamespace` request — no FastAPI app, no
TestClient, no Redis. Complements the end-to-end coverage in
tests/integration/test_rate_limit_headers.py.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.responses import JSONResponse
from starlette.responses import Response

from api.middleware.rate_limit import RateLimitMiddleware


class StubLimiter:
    """Records the args of every check_rate_limit() call for later inspection."""

    def __init__(self, allowed: bool = True, remaining: int = 59) -> None:
        self._allowed = allowed
        self._remaining = remaining
        self.calls: list[tuple[str, int, int]] = []

    def check_rate_limit(
        self, identifier: str, limit: int, window_seconds: int = 60
    ) -> tuple[bool, int]:
        self.calls.append((identifier, limit, window_seconds))
        return self._allowed, self._remaining


def _make_request(
    path: str = "/api/x",
    user_id: str | None = None,
    client_host: str | None = "127.0.0.1",
) -> Mock:
    """Synthesize a minimal object with just the attributes the middleware reads."""
    request = Mock()
    request.url = SimpleNamespace(path=path)
    request.state = SimpleNamespace()
    if user_id is not None:
        request.state.user_id = user_id
    request.client = SimpleNamespace(host=client_host) if client_host is not None else None
    return request


@pytest.mark.unit
class TestIdentifierFor:
    """Tests for RateLimitMiddleware._identifier_for()."""

    def test_prefers_user_id_when_set(self) -> None:
        request = _make_request(user_id="abc123", client_host="1.2.3.4")
        assert RateLimitMiddleware._identifier_for(request) == "user:abc123"

    def test_falls_back_to_ip_when_no_user_id(self) -> None:
        request = _make_request(client_host="1.2.3.4")
        assert RateLimitMiddleware._identifier_for(request) == "ip:1.2.3.4"

    def test_returns_ip_unknown_when_client_is_none(self) -> None:
        request = _make_request(client_host=None)
        assert RateLimitMiddleware._identifier_for(request) == "ip:unknown"

    def test_returns_ip_unknown_when_client_host_is_empty(self) -> None:
        request = _make_request(client_host="")
        assert RateLimitMiddleware._identifier_for(request) == "ip:unknown"


@pytest.mark.unit
class TestDispatch:
    """Tests for RateLimitMiddleware.dispatch()."""

    def _middleware(
        self, allowed: bool = True, remaining: int = 59, limit: int = 60, window_seconds: int = 60
    ) -> tuple[RateLimitMiddleware, StubLimiter]:
        limiter = StubLimiter(allowed=allowed, remaining=remaining)
        mw = RateLimitMiddleware(
            app=Mock(), limiter=limiter, limit=limit, window_seconds=window_seconds
        )
        return mw, limiter

    @pytest.mark.asyncio
    async def test_exempt_root_path_bypasses_limiter(self) -> None:
        mw, limiter = self._middleware()
        downstream = Response()
        call_next = AsyncMock(return_value=downstream)

        response = await mw.dispatch(_make_request(path="/"), call_next)

        assert response is downstream
        assert limiter.calls == []
        assert "X-RateLimit-Limit" not in response.headers
        assert "X-RateLimit-Remaining" not in response.headers

    @pytest.mark.asyncio
    async def test_exempt_health_path_bypasses_limiter(self) -> None:
        mw, limiter = self._middleware()
        call_next = AsyncMock(return_value=Response())

        await mw.dispatch(_make_request(path="/health"), call_next)

        assert limiter.calls == []

    @pytest.mark.asyncio
    async def test_allowed_request_stamps_headers_on_downstream_response(self) -> None:
        mw, _ = self._middleware(allowed=True, remaining=42, limit=100)
        downstream = Response()
        call_next = AsyncMock(return_value=downstream)

        response = await mw.dispatch(_make_request(client_host="1.2.3.4"), call_next)

        assert response is downstream
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "42"

    @pytest.mark.asyncio
    async def test_allowed_request_calls_limiter_with_ip_identifier(self) -> None:
        mw, limiter = self._middleware(limit=60, window_seconds=30)
        call_next = AsyncMock(return_value=Response())

        await mw.dispatch(_make_request(client_host="1.2.3.4"), call_next)

        assert limiter.calls == [("ip:1.2.3.4", 60, 30)]

    @pytest.mark.asyncio
    async def test_allowed_request_uses_user_id_when_available(self) -> None:
        mw, limiter = self._middleware()
        call_next = AsyncMock(return_value=Response())

        await mw.dispatch(_make_request(user_id="abc"), call_next)

        assert limiter.calls[0][0] == "user:abc"

    @pytest.mark.asyncio
    async def test_rejected_request_returns_429_with_headers(self) -> None:
        mw, _ = self._middleware(allowed=False, remaining=0, limit=60, window_seconds=60)
        call_next = AsyncMock()

        response = await mw.dispatch(_make_request(), call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 429
        assert response.headers["X-RateLimit-Limit"] == "60"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.headers["Retry-After"] == "60"

    @pytest.mark.asyncio
    async def test_rejected_request_does_not_call_downstream(self) -> None:
        mw, _ = self._middleware(allowed=False, remaining=0)
        call_next = AsyncMock()

        await mw.dispatch(_make_request(), call_next)

        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejected_retry_after_matches_configured_window(self) -> None:
        mw, _ = self._middleware(allowed=False, remaining=0, limit=10, window_seconds=30)

        response = await mw.dispatch(_make_request(), AsyncMock())

        assert response.headers["Retry-After"] == "30"

    @pytest.mark.asyncio
    async def test_rejected_response_body_is_json_with_detail(self) -> None:
        mw, _ = self._middleware(allowed=False, remaining=0)

        response = await mw.dispatch(_make_request(), AsyncMock())

        assert json.loads(response.body) == {"detail": "Rate limit exceeded"}

    @pytest.mark.asyncio
    async def test_header_values_are_strings_not_ints(self) -> None:
        """HTTP headers must be strings — regression guard against int leakage."""
        mw, _ = self._middleware(allowed=True, remaining=59, limit=60)
        response = await mw.dispatch(_make_request(), AsyncMock(return_value=Response()))
        assert isinstance(response.headers["X-RateLimit-Limit"], str)
        assert isinstance(response.headers["X-RateLimit-Remaining"], str)
