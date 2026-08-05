import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from safety.rate_limiter import RateLimiter

log = structlog.get_logger()

EXEMPT_PATHS = frozenset({"/", "/health"})


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces a rolling-window rate limit per client and
    attaches X-RateLimit-Limit / X-RateLimit-Remaining to every response.

    Behavior:
        - Exempt paths (root, /health) short-circuit and receive no headers.
        - If the limiter reports the request is over the limit, respond 429
          immediately with X-RateLimit-Limit, X-RateLimit-Remaining=0, and
          Retry-After; the downstream route is not invoked.
        - Otherwise call the downstream handler and set the two headers on
          the returned response.

    Identifier strategy:
        - Authenticated user id from request.state.user_id, if set upstream.
        - Otherwise the peer IP from request.client.host.
        - Otherwise the literal "unknown" (test clients where request.client
          is None).
    """

    def __init__(
        self,
        app: ASGIApp,
        limiter: RateLimiter,
        limit: int,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.limiter = limiter
        self.limit = limit
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        identifier = self._identifier_for(request)
        allowed, remaining = self.limiter.check_rate_limit(
            identifier=identifier,
            limit=self.limit,
            window_seconds=self.window_seconds,
        )

        if not allowed:
            log.info(
                "rate_limit_middleware_rejected",
                identifier=identifier,
                path=request.url.path,
                limit=self.limit,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(self.window_seconds),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    @staticmethod
    def _identifier_for(request: Request) -> str:
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        if request.client and request.client.host:
            return f"ip:{request.client.host}"
        return "ip:unknown"
