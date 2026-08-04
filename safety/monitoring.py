"""Safety event monitoring."""

import time

import redis
import structlog

logger = structlog.get_logger()


class SafetyMonitor:
    """Monitor and log safety events."""

    VALID_EVENT_TYPES = {
        "pii_detected",
        "injection_attempt",
        "content_filtered",
        "bias_detected",
        "rate_limited",
    }

    # Keep enough history to answer any reasonable window query; trim beyond this.
    RETENTION_SECONDS = 24 * 60 * 60  # 24 hours

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

        now = time.time()

        try:
            logger.warning("safety_event", event_type=event_type, **details)

            key = f"safety:events:{event_type}"
            # Score = timestamp, member must be unique per event.
            member = f"{now}:{details.get('id', id(details))}"
            self.redis.zadd(key, {member: now})

            # Trim anything older than our retention window so the set
            # doesn't grow unbounded, and set an expiry as a backstop.
            cutoff = now - self.RETENTION_SECONDS
            self.redis.zremrangebyscore(key, 0, cutoff)
            self.redis.expire(key, self.RETENTION_SECONDS)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def get_event_count(self, event_type: str, window_hours: int = 1) -> int:
        """Get count of safety events of a given type within a time window.

        Args:
            event_type: Type of event
            window_hours: Time window in hours, counted back from now

        Returns:
            Count of events in the window
        """
        key = f"safety:events:{event_type}"
        now = time.time()
        window_start = now - (window_hours * 3600)

        try:
            return self.redis.zcount(key, window_start, now)
        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0

    def get_total_event_count(self, window_hours: int = 1) -> int:
        """Get total count of safety events across all event types.

        Args:
            window_hours: Time window in hours, counted back from now

        Returns:
            Combined count across all event types in the window
        """
        total = 0
        for event_type in self.VALID_EVENT_TYPES:
            total += self.get_event_count(event_type, window_hours=window_hours)
        return total
