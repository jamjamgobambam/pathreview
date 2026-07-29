from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core.security import decode_access_token
from safety.rate_limiter import RateLimiter


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Enforces a per-user rolling-window rate limit for authenticated requests
    and attaches X-RateLimit-Limit / X-RateLimit-Remaining headers to every
    response.
    """

    def __init__(self, app, rate_limiter: RateLimiter, limit: int):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.limit = limit

    async def dispatch(self, request: Request, call_next) -> Response:
        identifier = None
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            if payload:
                identifier = payload.get("sub")

        if identifier is None:
            # JWT-only first pass: unauthenticated requests aren't rate
            # limited yet (IP fallback to be added later).
            return await call_next(request)

        allowed, remaining = self.rate_limiter.check_rate_limit(
            identifier=identifier,
            limit=self.limit,
            window_seconds=60,
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
