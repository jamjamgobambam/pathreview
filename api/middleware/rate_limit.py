"""HTTP middleware for API rate limiting."""

from fastapi import Request
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from safety.rate_limiter import RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce a per-client request limit and report the remaining quota."""

    def __init__(self, app: ASGIApp, rate_limiter: RateLimiter, limit: int) -> None:
        """Initialize the middleware.

        Args:
            app: Downstream ASGI application.
            rate_limiter: Limiter used to check each client identifier.
            limit: Maximum requests allowed per minute.
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.limit = limit

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Check the client quota and attach rate-limit headers to the response."""
        identifier = request.client.host if request.client is not None else "unknown"
        allowed, remaining = await run_in_threadpool(
            self.rate_limiter.check_rate_limit,
            identifier,
            self.limit,
        )

        if allowed:
            response = await call_next(request)
        else:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        return response
