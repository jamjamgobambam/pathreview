"""Safety event monitoring."""

import time
from uuid import uuid4

import redis
import structlog

logger = structlog.get_logger()


class SafetyMonitor:
    """Monitor and log safety events."""

    EVENT_KEY_PREFIX = "safety:events:timeline"
    RETENTION_SECONDS = 86400

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

    def log_event(self, event_type: str, details: dict[str, object]) -> None:
        """Log a safety event.

        Args:
            event_type: Type of event (from VALID_EVENT_TYPES)
            details: Event details dict
        """
        if event_type not in self.VALID_EVENT_TYPES:
            logger.warning("unknown_event_type", event_type=event_type)
            return

        timestamp = time.time()
        key = self._event_key(event_type)
        member = f"{timestamp}:{uuid4().hex}"

        try:
            # Log to structlog
            logger.warning("safety_event", event_type=event_type, **details)

            # Store timestamped events so rolling-window counts are accurate.
            self.redis.zadd(key, {member: timestamp})
            self.redis.expire(key, self.RETENTION_SECONDS)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def get_event_count(self, event_type: str, window_hours: int = 1) -> int:
        """Get count of safety events.

        Args:
            event_type: Type of event
            window_hours: Rolling time window in hours

        Returns:
            Count of events in the window
        """
        if event_type not in self.VALID_EVENT_TYPES or window_hours <= 0:
            return 0

        key = self._event_key(event_type)
        window_start = time.time() - (window_hours * 3600)

        try:
            self.redis.zremrangebyscore(key, "-inf", window_start)
            return int(self.redis.zcount(key, window_start, "+inf"))

        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0

    def get_total_event_count(self, window_hours: int = 1) -> int:
        """Return the total count across all valid safety event types.

        Args:
            window_hours: Rolling time window in hours

        Returns:
            Total safety events in the window
        """
        return sum(
            self.get_event_count(event_type, window_hours) for event_type in self.VALID_EVENT_TYPES
        )

    @classmethod
    def _event_key(cls, event_type: str) -> str:
        """Return the Redis key for an event type."""
        return f"{cls.EVENT_KEY_PREFIX}:{event_type}"
