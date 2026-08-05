"""Shared Redis client for dependency injection."""

from collections.abc import Generator

import redis

from core.config import settings

_redis_pool: redis.ConnectionPool = redis.ConnectionPool.from_url(
    settings.redis_url, decode_responses=True
)


def get_redis() -> Generator[redis.Redis, None, None]:
    """Dependency for FastAPI that yields a Redis client."""
    client = redis.Redis(connection_pool=_redis_pool)
    try:
        yield client
    finally:
        client.close()
