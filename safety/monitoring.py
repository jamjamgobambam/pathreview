"""Safety event monitoring."""

import time
import uuid

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

    def __init__(self, redis_client: redis.Redis):
        """Initialize safety monitor.

        Args:
            redis_client: Redis client
        """
        self.redis = redis_client

    def log_event(self, event_type: str, details: dict) -> None:
        """Log a safety event.

        Args:
            event_type: Type of event from VALID_EVENT_TYPES
            details: Event details dictionary
        """
        if event_type not in self.VALID_EVENT_TYPES:
            logger.warning("unknown_event_type", event_type=event_type)
            return

        try:
            logger.warning(
                "safety_event",
                event_type=event_type,
                **details,
            )

            # Store each event with its timestamp in a Redis sorted set.
            key = f"safety:events:{event_type}:timeline"
            timestamp = time.time()
            event_id = str(uuid.uuid4())

            self.redis.zadd(key, {event_id: timestamp})

            # Keep only events from the last 24 hours.
            twenty_four_hours_ago = timestamp - (24 * 60 * 60)
            self.redis.zremrangebyscore(key, 0, twenty_four_hours_ago)

            # Remove the Redis key after 24 hours without activity.
            self.redis.expire(key, 86400)

        except Exception as exc:
            logger.error(
                "safety_monitor_error",
                event_type=event_type,
                error=str(exc),
            )

    def get_event_count(self, event_type: str, window_hours: int = 1) -> int:
        """Get the number of events within a time window.

        Args:
            event_type: Type of safety event
            window_hours: Number of previous hours to include

        Returns:
            Number of matching events in the requested time window
        """
        if event_type not in self.VALID_EVENT_TYPES:
            logger.warning("unknown_event_type", event_type=event_type)
            return 0

        if window_hours <= 0:
            return 0

        key = f"safety:events:{event_type}:timeline"
        current_time = time.time()
        cutoff_time = current_time - (window_hours * 60 * 60)

        try:
            return int(
                self.redis.zcount(
                    key,
                    cutoff_time,
                    current_time,
                )
            )

        except Exception as exc:
            logger.error(
                "event_count_error",
                event_type=event_type,
                error=str(exc),
            )
            return 0

    def get_total_event_count(self, window_hours: int = 1) -> int:
        """Get the total number of all safety events within a time window.

        Args:
            window_hours: Number of previous hours to include

        Returns:
            Total number of safety events in the requested time window
        """
        return sum(
            self.get_event_count(event_type, window_hours) for event_type in self.VALID_EVENT_TYPES
        )
