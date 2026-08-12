"""Middleware that rate-limits every request by client IP, and additionally
by authenticated user when a valid JWT is present."""

import redis
import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from core.config import settings
from core.security import decode_access_token
from safety.rate_limiter import RateLimiter

log = structlog.get_logger()

_redis_client = redis.Redis.from_url(settings.redis_url)
_rate_limiter = RateLimiter(_redis_client)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate-limits requests per client IP, and per authenticated user when
    an `Authorization: Bearer <jwt>` header decodes successfully.

    The IP layer always applies, since it's the only identifier available
    for anonymous traffic. The user layer is an additional check so one
    heavy authenticated user can't hide inside a shared IP bucket. Either
    layer being over its limit short-circuits with a 429.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        allowed, _ = _rate_limiter.check_rate_limit(
            f"ip:{client_ip}", limit=settings.rate_limit_per_minute
        )
        if not allowed:
            return self._rate_limited_response(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
            payload = decode_access_token(token)
            if payload is not None and (sub := payload.get("sub")):
                allowed, _ = _rate_limiter.check_rate_limit(
                    f"user:{sub}", limit=settings.rate_limit_per_minute
                )
                if not allowed:
                    return self._rate_limited_response(request)

        return await call_next(request)

    def _rate_limited_response(self, request: Request) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "request_id": request_id,
            },
        )
