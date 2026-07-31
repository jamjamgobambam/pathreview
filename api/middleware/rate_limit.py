import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from core.config import settings
from core.redis import redis_client
from core.security import decode_access_token
from safety.rate_limiter import RateLimiter

log = structlog.get_logger()

EXCLUDED_PATHS = {"/health"}


def _identify_request(request: Request) -> str:
    """Pick a rate-limit identifier for a request.

    Args:
        request: Incoming request.

    Returns:
        `user:<id>` if the request carries a valid Bearer token, otherwise
        `ip:<client_ip>`.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            return f"user:{payload['sub']}"

    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces a per-identifier rolling-window rate limit and
    stamps X-RateLimit-Limit / X-RateLimit-Remaining on every response.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.limiter = RateLimiter(redis_client)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Enforce the rate limit and stamp rate-limit headers on the response.

        Args:
            request: Incoming request.
            call_next: Passes the request to the next handler in the chain.

        Returns:
            The downstream response (or a 429 JSON response if the caller is
            over their limit), with X-RateLimit-Limit and X-RateLimit-Remaining
            headers attached either way.
        """
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        identifier = _identify_request(request)
        limit = settings.rate_limit_per_minute
        allowed, remaining = self.limiter.check_rate_limit(identifier, limit)

        if not allowed:
            log.warning("rate_limit_blocked", identifier=identifier, path=request.url.path)
            response: Response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )
        else:
            response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
