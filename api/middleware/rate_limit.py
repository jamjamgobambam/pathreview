import redis
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from core.config import settings
from core.security import decode_access_token
from safety.rate_limiter import RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces a per-identifier rate limit and attaches
    X-RateLimit-Limit / X-RateLimit-Remaining headers to every response.

    Identifier resolution: the `sub` claim of a valid Bearer token if
    present, otherwise the client IP address.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        self.limiter = RateLimiter(redis_client)

    def _resolve_identifier(self, request: Request) -> str:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            payload = decode_access_token(token)
            if payload is not None:
                sub = payload.get("sub")
                if sub:
                    return str(sub)

        if request.client is not None:
            return str(request.client.host)

        return "unknown"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        identifier = self._resolve_identifier(request)
        limit = settings.rate_limit_per_minute
        allowed, remaining = self.limiter.check_rate_limit(identifier, limit)

        if not allowed:
            response: Response = JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded: {limit} requests per minute allowed"},
            )
        else:
            response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
