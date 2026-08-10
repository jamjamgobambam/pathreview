import redis
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from core.config import settings
from safety.rate_limiter import RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply API rate limits and expose rate-limit response headers."""

    def __init__(self, app):
        super().__init__(app)

        redis_client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

        self.rate_limiter = RateLimiter(redis_client)
        self.limit = settings.rate_limit_per_minute

    async def dispatch(self, request: Request, call_next) -> Response:
        identifier = request.client.host if request.client is not None else "unknown"

        allowed, remaining = self.rate_limiter.check_rate_limit(
            identifier=identifier,
            limit=self.limit,
            window_seconds=60,
        )

        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(remaining),
        }

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
                headers=headers,
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
