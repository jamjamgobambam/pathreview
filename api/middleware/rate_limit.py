from collections.abc import Awaitable, Callable

import redis
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from core.config import settings
from safety.rate_limiter import RateLimiter

rate_limiter = RateLimiter(redis_client=redis.Redis.from_url(settings.redis_url))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that calls the check_rate_limit function and returns either a 429 error
    if the user has gone above the limit or a response otherwise. Both outputs include
    X-RateLimit-Limit and X-RateLimit-Remaining headers to inform the user of their
    current usage.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize BaseHTTPMiddleware app instance.

        Args:
            app: BaseHTTPMiddleware app
        """
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Overrides BaseHTTPMiddleware dispatch to run
        the check_rate_limiter function.

        Args:
            request: FastAPI Request body
            call_next: Function that invokes the next middleware or route

        Returns:
            Downstream FastAPI Response or 429 error if request limit exceeded
            with X-RateLimit-Limit and X-RateLimit-Remaining headers added.

        """
        identifier = request.client.host if request.client else "unknown"
        limit = settings.rate_limit_per_minute

        allowed, remaining = rate_limiter.check_rate_limit(
            identifier=identifier,
            limit=limit,
            window_seconds=60,
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Request limit exceeded"},
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
