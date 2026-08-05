"""Redis connection management and dependency injection."""

import redis
import structlog

from core.config import settings

log = structlog.get_logger()


def get_redis() -> redis.Redis:
    """Dependency for FastAPI that provides a Redis client.

    Returns:
        A connected Redis client instance.

    Raises:
        ConnectionError: If Redis connection fails.
    """
    try:
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        log.debug("redis_connection_established")
        return client
    except Exception as e:
        log.error("redis_connection_failed", error=str(e))
        raise ConnectionError(f"Failed to connect to Redis: {str(e)}") from e
