from collections.abc import Awaitable, Callable

import redis
import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings
from safety.rate_limiter import RateLimiter

log = structlog.get_logger()


class IPRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that rate limits requests per client IP address.

    This is a secondary layer on top of any per-user rate limiting,
    so unauthenticated requests are still bounded.
    """

    def __init__(self, app: object, limit: int | None = None, window_seconds: int = 60) -> None:
        super().__init__(app)
        redis_client = redis.Redis.from_url(settings.redis_url)
        self.limiter = RateLimiter(redis_client)
        self.limit = limit if limit is not None else settings.rate_limit_per_minute
        self.window_seconds = window_seconds

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        allowed, remaining = self.limiter.check_rate_limit(
            f"ip:{client_ip}", limit=self.limit, window_seconds=self.window_seconds
        )

        if not allowed:
            log.warning("ip_rate_limit_exceeded", ip=client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
