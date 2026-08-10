import uuid
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from api.main import app
from api.middleware.rate_limit import rate_limit
from core.redis_client import redis_client


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Override the rate_limit dependency to use a unique identifier per
    test, so tests never share Redis rate-limit state with each other,
    with manual curl testing, or with a live dev server hitting the same
    Redis instance from a separate process.
    """
    test_id = str(uuid.uuid4())

    async def rate_limit_override() -> None:
        from core.config import settings
        from safety.rate_limiter import RateLimiter

        limiter = RateLimiter(redis_client)
        allowed, _ = limiter.check_rate_limit(
            identifier=f"test:{test_id}",
            limit=settings.rate_limit_ip_per_minute,
            window_seconds=60,
        )
        if not allowed:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

    app.dependency_overrides[rate_limit] = rate_limit_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(rate_limit, None)
    for key in redis_client.scan_iter(f"rate_limit:test:{test_id}*"):
        redis_client.delete(key)
