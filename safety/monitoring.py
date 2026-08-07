"""Safety event monitoring."""

import redis
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()


class SafetyMonitor:
    """Monitor and log safety events."""

    # Valid event types
    VALID_EVENT_TYPES = {
        "pii_detected",
        "injection_attempt",
        "content_filtered",
        "bias_detected",
        "rate_limited"
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

        now = datetime.utcnow()
        timestamp = now.isoformat()

        try:
            # Log to structlog
            logger.warning("safety_event", event_type=event_type, **details)

            # Store count in an hourly bucket so it can later be scoped to a
            # specific time window (e.g. "last hour") instead of an
            # unbounded/rolling total.
            key = self._hour_bucket_key(event_type, now)
            self.redis.incr(key)
            # Keep buckets around for 48 hours, comfortably longer than any
            # window we currently query, then let them expire.
            self.redis.expire(key, 172800)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def _hour_bucket_key(self, event_type: str, when: datetime) -> str:
        """Build the Redis key for the hourly bucket containing `when`."""
        hour_bucket = when.strftime("%Y%m%d%H")
        return f"safety:events:{event_type}:{hour_bucket}"

    def get_event_count(self, event_type: str, window_hours: int = 1) -> int:
        """Get count of safety events of a given type in the last `window_hours`.

        Args:
            event_type: Type of event
            window_hours: Time window in hours to sum counts over

        Returns:
            Count of events in the window
        """
        now = datetime.utcnow()
        total = 0

        try:
            for i in range(window_hours):
                bucket_time = now - timedelta(hours=i)
                key = self._hour_bucket_key(event_type, bucket_time)
                count = self.redis.get(key)
                if count:
                    total += int(count)
            return total

        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0

    def get_total_event_count(self, window_hours: int = 1) -> int:
        """Get count of safety events across all event types in the last
        `window_hours`.

        Args:
            window_hours: Time window in hours to sum counts over

        Returns:
            Total count of events of any type in the window
        """
        total = 0
        for event_type in self.VALID_EVENT_TYPES:
            total += self.get_event_count(event_type, window_hours=window_hours)
        return total
