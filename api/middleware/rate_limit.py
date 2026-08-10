"""Rate limiting dependency: per-user for authenticated requests, per-IP otherwise."""

from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from core.config import settings
from core.redis_client import get_redis
from core.security import decode_access_token
from safety.rate_limiter import RateLimiter

log = structlog.get_logger()

# Reuse the same scheme as auth.py, but don't require a token —
# unauthenticated requests should fall back to IP-based limiting instead of 401ing here.
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _get_client_ip(request: Request) -> str:
    """Extract the client IP, checking common proxy headers first.

    Falls back to request.client.host if no proxy headers are present.
    Note: X-Forwarded-For can be spoofed by the client unless the app is
    behind a trusted proxy that overwrites it — acceptable for this app's
    current deployment, but worth hardening later if a real reverse proxy
    is introduced.
    """
    forwarded_for: str | None = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # X-Forwarded-For can be a comma-separated list; the first entry
        # is the original client.
        return str(forwarded_for.split(",")[0].strip())
    real_ip: str | None = request.headers.get("x-real-ip")
    if real_ip:
        return str(real_ip)
    if request.client:
        return str(request.client.host)
    return "unknown"


async def rate_limit(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme_optional)] = None,
) -> None:
    """FastAPI dependency that rate limits by user ID (if authenticated)
    or by client IP (if not). Raises 429 if the limit is exceeded.
    """
    limiter = RateLimiter(get_redis())

    identifier: str | None = None
    if token:
        payload = decode_access_token(token)
        if payload:
            identifier = payload.get("sub")

    if identifier:
        # Authenticated request — limit per user.
        allowed, remaining = limiter.check_rate_limit(
            identifier=f"user:{identifier}",
            limit=settings.rate_limit_per_minute,
            window_seconds=60,
        )
    else:
        # Unauthenticated request — limit per IP.
        ip = _get_client_ip(request)
        allowed, remaining = limiter.check_rate_limit(
            identifier=f"ip:{ip}",
            limit=settings.rate_limit_ip_per_minute,
            window_seconds=60,
        )

    if not allowed:
        log.warning("rate_limit_exceeded_request_blocked", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )
