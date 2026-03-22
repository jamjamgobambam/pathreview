"""Rate limiting with rolling window."""

import redis
import time
import structlog

logger = structlog.get_logger()


class RateLimiter:
    """Rate limiter using Redis sorted sets for rolling window."""

    def __init__(self, redis_client: redis.Redis):
        """Initialize rate limiter.

        Args:
            redis_client: Redis client
        """
        self.redis = redis_client

    def check_rate_limit(self, identifier: str, limit: int,
                        window_seconds: int = 60) -> tuple[bool, int]:
        """Check if request is within rate limit.

        Args:
            identifier: Request identifier (user_id, ip_address, etc.)
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed, remaining_requests)
        """
        key = f"rate_limit:{identifier}"
        now = time.time()
        window_start = now - window_seconds

        try:
            # Remove old entries outside the window
            self.redis.zremrangebyscore(key, 0, window_start)

            # Count current requests in window
            current_count = self.redis.zcard(key)

            if current_count < limit:
                # Add this request
                self.redis.zadd(key, {str(now): now})
                self.redis.expire(key, window_seconds + 1)
                remaining = limit - current_count - 1

                logger.info("rate_limit_allowed", identifier=identifier,
                           current_count=current_count + 1, limit=limit)
                return True, remaining

            else:
                # Rate limit exceeded
                logger.warning("rate_limit_exceeded", identifier=identifier,
                             limit=limit)
                return False, 0

        except Exception as e:
            logger.error("rate_limiter_error", identifier=identifier, error=str(e))
            # Fail open on Redis error
            return True, limit
