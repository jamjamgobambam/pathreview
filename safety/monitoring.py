"""Safety event monitoring."""

import time
import uuid

import redis
import structlog

logger = structlog.get_logger()


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

        Records the event in a Redis sorted set keyed by event type, using the
        current timestamp as the score so that occurrences can be counted over a
        rolling time window. The member appends a UUID to the timestamp because
        sorted-set members must be unique: two events logged within the same
        timestamp would otherwise collide, silently overwriting each other and
        undercounting. The key expires after 24 hours.

        Args:
            event_type: Type of event (from VALID_EVENT_TYPES)
            details: Event details dict
        """
        if event_type not in self.VALID_EVENT_TYPES:
            logger.warning("unknown_event_type", event_type=event_type)
            return

        try:
            # Log to structlog
            logger.warning("safety_event", event_type=event_type, **details)

            # Store event in a sorted set scored by timestamp for windowed counts
            key = f"safety:events:z:{event_type}"
            now = time.time()
            self.redis.zadd(key, {f"{now}:{uuid.uuid4()}": now})
            # Set expiry to 24 hours
            self.redis.expire(key, 86400)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def get_event_count(self, event_type: str, window_hours: int = 1) -> int:
        """Get count of safety events within a rolling time window.

        Drops entries older than the window from the sorted set, then counts
        the remaining entries. Returns 0 if no events have been recorded.

        Args:
            event_type: Type of event
            window_hours: Time window in hours

        Returns:
            Count of events in the window
        """
        key = f"safety:events:z:{event_type}"
        window_start = time.time() - (window_hours * 3600)

        try:
            # Remove entries outside the window
            self.redis.zremrangebyscore(key, 0, window_start)

            # Count remaining entries in the window
            return self.redis.zcard(key)

        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0
