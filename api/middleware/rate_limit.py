"""Rate limiting middleware enforcing per-IP and per-user budgets."""

import ipaddress

import redis
import structlog
from fastapi import Request
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from core.security import decode_access_token
from safety.rate_limiter import RateLimiter

log = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces rolling-window rate limits on incoming requests.

    Every non-exempt request consumes a per-IP budget. Requests carrying a
    valid Bearer token also consume a separate per-user budget and must pass
    both checks. Redis failures fail open inside RateLimiter, so rate
    limiting never takes the API down when Redis is unavailable.
    """

    def __init__(
        self,
        app: ASGIApp,
        redis_client: redis.Redis,
        limit: int,
        window_seconds: int = 60,
        trust_proxy: bool = False,
        exempt_paths: tuple[str, ...] = ("/health",),
    ) -> None:
        """Initialize the middleware.

        Args:
            app: The wrapped ASGI application
            redis_client: Redis client backing the rate limiter
            limit: Maximum requests allowed per identifier per window
            window_seconds: Rolling window length in seconds
            trust_proxy: Trust the first valid X-Forwarded-For address.
                Enable only when a proxy in front of the API overwrites
                the header; otherwise clients could spoof their identity.
            exempt_paths: Exact request paths that bypass rate limiting
        """
        super().__init__(app)
        self.limiter = RateLimiter(redis_client)
        self.limit = limit
        self.window_seconds = window_seconds
        self.trust_proxy = trust_proxy
        self.exempt_paths = exempt_paths

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Check the IP budget, then the user budget when authenticated."""
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # check_rate_limit uses the synchronous Redis client, so it runs in
        # the threadpool to keep Redis round trips off the event loop.
        ip_allowed, _ = await run_in_threadpool(
            self.limiter.check_rate_limit,
            f"ip:{self._client_ip(request)}",
            self.limit,
            self.window_seconds,
        )
        if not ip_allowed:
            return self._rate_limited_response()

        user_id = self._extract_user_id(request)
        if user_id is not None:
            user_allowed, _ = await run_in_threadpool(
                self.limiter.check_rate_limit,
                f"user:{user_id}",
                self.limit,
                self.window_seconds,
            )
            if not user_allowed:
                return self._rate_limited_response()

        return await call_next(request)

    def _client_ip(self, request: Request) -> str:
        """Return the client address used for the per-IP budget.

        Uses the direct peer address by default. When trust_proxy is enabled,
        the first valid address in X-Forwarded-For takes precedence; invalid
        values are logged and ignored.
        """
        if self.trust_proxy:
            forwarded: str = request.headers.get("X-Forwarded-For", "")
            candidate: str = forwarded.split(",")[0].strip()
            if candidate:
                try:
                    ipaddress.ip_address(candidate)
                except ValueError:
                    log.warning("rate_limit_invalid_forwarded_for", value=candidate)
                else:
                    return candidate
        if request.client is not None and request.client.host:
            host: str = request.client.host
            return host
        return "unknown"

    def _extract_user_id(self, request: Request) -> str | None:
        """Return the authenticated user id, or None for anonymous traffic.

        Any missing, malformed, expired, or undecodable Bearer token means
        the request is treated as IP-only traffic rather than rejected.
        """
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None
        try:
            payload = decode_access_token(token)
        except Exception as exc:
            log.warning("rate_limit_token_decode_failed", error=str(exc))
            return None
        if payload is None:
            return None
        user_id = payload.get("sub")
        if isinstance(user_id, str) and user_id:
            return user_id
        return None

    def _rate_limited_response(self) -> Response:
        """Build the 429 response for a request over budget.

        Retry-After is the fixed window length because check_rate_limit
        reports a remaining request count, not seconds until reset.
        """
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={
                "Retry-After": str(self.window_seconds),
                "X-RateLimit-Limit": str(self.limit),
                "X-RateLimit-Remaining": "0",
            },
        )
