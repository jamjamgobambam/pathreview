"""Middleware enforcing per-IP and per-user request rate limits."""

from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from core.security import decode_access_token
from safety.rate_limiter import RateLimiter

log = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limits every request by client IP address, and additionally by
    user ID when the request carries a valid bearer token.

    The IP-based check runs for every request, authenticated or not, so
    unauthenticated traffic to public endpoints can't flood the API just
    because it has no user ID to key off of.
    """

    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: RateLimiter,
        ip_limit: int,
        user_limit: int,
        window_seconds: int = 60,
        exclude_paths: frozenset[str] = frozenset({"/health", "/"}),
    ) -> None:

        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.ip_limit = ip_limit
        self.user_limit = user_limit
        self.window_seconds = window_seconds
        self.exclude_paths = exclude_paths

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        allowed, _ = self.rate_limiter.check_rate_limit(
            f"ip:{client_ip}", limit=self.ip_limit, window_seconds=self.window_seconds
        )
        if not allowed:
            log.warning(
                "rate_limit_blocked", scope="ip", client_ip=client_ip, path=request.url.path
            )
            return self._too_many_requests()

        user_id = self._extract_user_id(request)
        if user_id is not None:
            allowed, _ = self.rate_limiter.check_rate_limit(
                f"user:{user_id}", limit=self.user_limit, window_seconds=self.window_seconds
            )
            if not allowed:
                log.warning(
                    "rate_limit_blocked", scope="user", user_id=user_id, path=request.url.path
                )
                return self._too_many_requests()

        return await call_next(request)

    @staticmethod
    def _extract_user_id(request: Request) -> str | None:
        """Best-effort extraction of the user ID from a bearer token.

        Runs ahead of the `get_current_user` dependency, so invalid or
        missing tokens are simply treated as unauthenticated rather than
        rejected here.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        payload = decode_access_token(auth_header.removeprefix("Bearer "))
        if payload is None:
            return None

        user_id = payload.get("sub")
        return str(user_id) if user_id is not None else None

    def _too_many_requests(self) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."},
            headers={"Retry-After": str(self.window_seconds)},
        )
