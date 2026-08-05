"""Safety event monitoring."""

import time
from datetime import datetime
from uuid import uuid4

import redis
import structlog

logger = structlog.get_logger()

# Sorted set of individual event timestamps, one key per event type. Scored by
# epoch seconds so counts can be taken over an arbitrary rolling window.
RECENT_EVENTS_KEY_PREFIX = "safety:events:recent"

# How long individual events are kept for windowed counts.
EVENT_RETENTION_SECONDS = 86400

# Default rolling window used by get_safety_events_last_hour().
DEFAULT_WINDOW_SECONDS = 3600


class SafetyMonitor:
    """Monitor and log safety events."""

    # Valid event types
    VALID_EVENT_TYPES = {
        "pii_detected",
        "injection_attempt",
        "content_filtered",
        "bias_detected",
        "rate_limited",
    }

    def __init__(self, redis_client: redis.Redis):
        """Initialize safety monitor.

        Args:
            redis_client: Redis client
        """
        self.redis = redis_client

    def log_event(self, event_type: str, details: dict) -> None:
        """Log a safety event.

        Args:
            event_type: Type of event (from VALID_EVENT_TYPES)
            details: Event details dict
        """
        if event_type not in self.VALID_EVENT_TYPES:
            logger.warning("unknown_event_type", event_type=event_type)
            return

        timestamp = datetime.utcnow().isoformat()

        try:
            # Log to structlog
            logger.warning("safety_event", event_type=event_type, **details)

            # Store count in Redis for monitoring
            key = f"safety:events:{event_type}"
            self.redis.incr(key)
            # Set expiry to 24 hours
            self.redis.expire(key, 86400)

            # Record the individual event so it can be counted over a rolling
            # window. The member must be unique or ZADD would overwrite a
            # same-timestamp event instead of adding one.
            now = time.time()
            recent_key = f"{RECENT_EVENTS_KEY_PREFIX}:{event_type}"
            self.redis.zadd(recent_key, {f"{timestamp}:{uuid4().hex[:8]}": now})
            # Drop events that have aged out of the retention period
            self.redis.zremrangebyscore(recent_key, 0, now - EVENT_RETENTION_SECONDS)
            self.redis.expire(recent_key, EVENT_RETENTION_SECONDS + 60)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def get_event_count(self, event_type: str, window_hours: int = 1) -> int:
        """Get count of safety events.

        Args:
            event_type: Type of event
            window_hours: Time window in hours (not enforced here; for reference)

        Returns:
            Count of events in the window
        """
        key = f"safety:events:{event_type}"

        try:
            count = self.redis.get(key)
            return int(count) if count else 0

        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0

    def get_events_in_window(self, window_seconds: int = DEFAULT_WINDOW_SECONDS) -> int:
        """Count safety events of every type within a rolling window.

        Only events whose timestamp falls strictly after ``now - window_seconds``
        are counted, so an event exactly on the boundary is treated as expired.

        Args:
            window_seconds: Size of the rolling window, in seconds

        Returns:
            Total number of events across all event types in the window

        Raises:
            redis.RedisError: If Redis is unreachable. Callers that must not
                fail (the health endpoint) are expected to catch this.
        """
        window_start = time.time() - window_seconds

        # One round trip for all event types
        pipe = self.redis.pipeline()
        for event_type in sorted(self.VALID_EVENT_TYPES):
            # The "(" prefix makes the lower bound exclusive
            pipe.zcount(f"{RECENT_EVENTS_KEY_PREFIX}:{event_type}", f"({window_start}", "+inf")

        return sum(pipe.execute())


_redis_client: redis.Redis | None = None


def _get_redis_client() -> redis.Redis:
    """Return a lazily created, process-wide Redis client.

    Imported locally so that this module stays importable without application
    config, and so callers can keep injecting their own client.
    """
    global _redis_client

    if _redis_client is None:
        from core.config import settings

        _redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    return _redis_client


def get_safety_events_last_hour(redis_client: redis.Redis | None = None) -> int:
    """Total number of safety events logged in the last hour.

    Args:
        redis_client: Redis client to use. Defaults to a shared client built
            from ``settings.redis_url``.

    Returns:
        Count of events strictly within the last hour

    Raises:
        redis.RedisError: If Redis is unreachable or the count fails.
    """
    monitor = SafetyMonitor(redis_client or _get_redis_client())
    return monitor.get_events_in_window(DEFAULT_WINDOW_SECONDS)
