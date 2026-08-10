import redis
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core.config import settings
from safety.rate_limiter import RateLimiter

log = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces a rolling-window rate limit per client and
    attaches `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers to
    every response so API clients can see their quota before hitting 429.
    """

    def __init__(self, app, redis_client: redis.Redis | None = None):
        super().__init__(app)
        self.limiter = RateLimiter(redis_client or redis.from_url(settings.redis_url))
        self.limit = settings.rate_limit_per_minute

    async def dispatch(self, request: Request, call_next) -> Response:
        identifier = request.client.host if request.client else "unknown"

        allowed, remaining = self.limiter.check_rate_limit(identifier, limit=self.limit)

        if not allowed:
            log.warning("rate_limit_response_blocked", identifier=identifier)
            response = Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
            )
        else:
            response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(remaining, 0))

        return response
