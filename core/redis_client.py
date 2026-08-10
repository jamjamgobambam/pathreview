"""Redis client for rate limiting and caching."""

import redis

from core.config import settings

# Create shared Redis client (singleton, following the database.py pattern)
redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def get_redis() -> redis.Redis:
    """Dependency for FastAPI that returns the shared Redis client."""
    return redis_client
