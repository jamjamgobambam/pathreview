"""HTTP middleware that enforces per-IP (and optional per-user) rate limits."""

from collections.abc import Awaitable, Callable

import redis
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from core.config import settings
from core.security import decode_access_token
from safety.rate_limiter import RateLimiter

log = structlog.get_logger()

# Paths that should never consume rate-limit budget (probes / OpenAPI).
_EXEMPT_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc")

CallNext = Callable[[Request], Awaitable[Response]]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce rolling-window rate limits using client IP and optional user ID.

    Unauthenticated requests are limited by IP only. When a valid Bearer JWT is
    present, both the IP and the token ``sub`` claim are checked.
    """

    def __init__(self, app: ASGIApp, redis_client: redis.Redis | None = None):
        """Initialize middleware.

        Args:
            app: ASGI application.
            redis_client: Optional Redis client (injected for tests). When
                omitted, connects using ``settings.redis_url``.
        """
        super().__init__(app)
        client = redis_client or redis.from_url(settings.redis_url)
        self.limiter = RateLimiter(client)
        self.limit = settings.rate_limit_per_minute
        self.window_seconds = 60

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        """Check the rate limit before forwarding the request.

        Args:
            request: Incoming HTTP request.
            call_next: Next ASGI handler in the middleware stack.

        Returns:
            Downstream response, or HTTP 429 when the limit is exceeded.
        """
        if request.method.upper() == "OPTIONS" or self._is_exempt(request.url.path):
            return await call_next(request)

        ip_address = self._client_ip(request)
        identifier = self._optional_user_id(request)

        allowed, _remaining = self.limiter.check_rate_limit(
            identifier,
            limit=self.limit,
            window_seconds=self.window_seconds,
            ip_address=ip_address,
        )

        if not allowed:
            request_id = getattr(request.state, "request_id", None)
            content: dict[str, str] = {
                "detail": "Rate limit exceeded. Try again later.",
            }
            if request_id is not None:
                content["request_id"] = str(request_id)
            log.warning(
                "rate_limit_middleware_denied",
                ip_address=ip_address,
                identifier=identifier,
                path=request.url.path,
            )
            return JSONResponse(status_code=429, content=content)

        return await call_next(request)

    @staticmethod
    def _is_exempt(path: str) -> bool:
        """Return True when the path should skip rate limiting.

        The root path ``/`` is an exact match only (not a prefix), so other
        routes are still rate limited.
        """
        if path == "/":
            return True
        return any(path == prefix or path.startswith(prefix + "/") for prefix in _EXEMPT_PREFIXES)

    @staticmethod
    def _client_ip(request: Request) -> str:
        """Extract client IP from the connection peer address."""
        if request.client is None:
            return "unknown"
        return request.client.host or "unknown"

    @staticmethod
    def _optional_user_id(request: Request) -> str | None:
        """Soft-decode Bearer JWT ``sub`` without requiring authentication."""
        auth = request.headers.get("Authorization")
        if not auth or not auth.lower().startswith("bearer "):
            return None
        token = auth.split(" ", 1)[1].strip()
        if not token:
            return None
        payload = decode_access_token(token)
        if payload is None:
            return None
        sub = payload.get("sub")
        return str(sub) if sub is not None else None
