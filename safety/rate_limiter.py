"""Rate limiting with rolling window."""

import time
import uuid

import redis
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

    def _window_count(self, key: str, now: float, window_seconds: int) -> int:
        """Remove expired entries and return the current window count.

        Args:
            key: Redis sorted-set key for this identifier.
            now: Current Unix timestamp.
            window_seconds: Rolling window size in seconds.

        Returns:
            Number of requests currently in the window.
        """
        window_start = now - window_seconds
        self.redis.zremrangebyscore(key, 0, window_start)
        return int(self.redis.zcard(key))

    @staticmethod
    def _entry_member(now: float) -> str:
        """Build a unique sorted-set member for a request at ``now``."""
        return f"{now}:{uuid.uuid4()}"

    def check_rate_limit(
        self,
        identifier: str | None,
        limit: int,
        window_seconds: int = 60,
        *,
        ip_address: str,
    ) -> tuple[bool, int]:
        """Check if a request is within rate limits for IP and optional user.

        Checks the IP address bucket first, then the primary identifier (e.g.
        user ID) when provided. Both buckets are recorded only when the request
        is allowed. Unauthenticated requests (``identifier is None``) are
        limited by IP only.

        Redis keys use distinct prefixes (``rate_limit:ip:`` /
        ``rate_limit:user:``) so an IP string never collides with a user id.
        Each recorded request uses a unique sorted-set member so concurrent
        requests at the same timestamp are counted separately.

        Args:
            identifier: Primary request identifier such as a user ID, or None
                for unauthenticated requests.
            limit: Maximum requests allowed in the window per bucket.
            window_seconds: Time window in seconds.
            ip_address: Client IP address used as a secondary rate-limit key.

        Returns:
            Tuple of (allowed, remaining_requests). Remaining is the minimum
            across applicable buckets. On Redis errors, fails open with
            ``(True, limit)``.
        """
        ip_key = f"rate_limit:ip:{ip_address}"
        user_key = f"rate_limit:user:{identifier}" if identifier is not None else None
        now = time.time()

        try:
            ip_count = self._window_count(ip_key, now, window_seconds)
            if ip_count >= limit:
                logger.warning(
                    "rate_limit_exceeded",
                    identifier=identifier,
                    ip_address=ip_address,
                    limit=limit,
                    bucket="ip",
                )
                return False, 0

            user_count = 0
            if user_key is not None:
                user_count = self._window_count(user_key, now, window_seconds)
                if user_count >= limit:
                    logger.warning(
                        "rate_limit_exceeded",
                        identifier=identifier,
                        ip_address=ip_address,
                        limit=limit,
                        bucket="user",
                    )
                    return False, 0

            member = self._entry_member(now)
            pipe = self.redis.pipeline()
            pipe.zadd(ip_key, {member: now})
            pipe.expire(ip_key, window_seconds + 1)
            if user_key is not None:
                pipe.zadd(user_key, {member: now})
                pipe.expire(user_key, window_seconds + 1)
            pipe.execute()

            ip_remaining = limit - ip_count - 1
            if user_key is not None:
                user_remaining = limit - user_count - 1
                remaining = min(ip_remaining, user_remaining)
            else:
                remaining = ip_remaining

            logger.info(
                "rate_limit_allowed",
                identifier=identifier,
                ip_address=ip_address,
                remaining=remaining,
                limit=limit,
            )
            return True, remaining

        except Exception as e:
            logger.error(
                "rate_limiter_error",
                identifier=identifier,
                ip_address=ip_address,
                error=str(e),
            )
            # Fail open on Redis error
            return True, limit
