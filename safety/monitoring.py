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

        Args:
            event_type: Type of event (from VALID_EVENT_TYPES)
            details: Event details dict
        """
        if event_type not in self.VALID_EVENT_TYPES:
            logger.warning("unknown_event_type", event_type=event_type)
            return

        timestamp = time.time()

        try:
            # Log to structlog
            logger.warning("safety_event", event_type=event_type, **details)

            # Store in a sorted set, scored by timestamp, so we can later
            # count events within an arbitrary trailing window (e.g. "last
            # 24 hours") instead of a counter whose TTL keeps resetting on
            # every new event and never actually expires under steady load.
            key = f"safety:events:{event_type}"
            member = f"{timestamp}:{uuid.uuid4().hex}"
            self.redis.zadd(key, {member: timestamp})

            # Drop entries older than 24h so the set doesn't grow unbounded.
            cutoff = timestamp - 86400
            self.redis.zremrangebyscore(key, 0, cutoff)
            self.redis.expire(key, 86400)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def get_event_count(self, event_type: str, window_hours: int = 24) -> int:
        """Get count of safety events within a trailing time window.

        Args:
            event_type: Type of event
            window_hours: Trailing time window in hours

        Returns:
            Count of events within the window
        """
        key = f"safety:events:{event_type}"
        cutoff = time.time() - (window_hours * 3600)

        try:
            return self.redis.zcount(key, cutoff, "+inf")

        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0

    def get_total_event_count(self, window_hours: int = 24) -> int:
        """Get total count of safety events across all categories within a
        trailing time window, using a single batched Redis pipeline.

        Args:
            window_hours: Trailing time window in hours

        Returns:
            Total aggregated event count across all categories within the window.
        """
        cutoff = time.time() - (window_hours * 3600)

        try:
            pipe = self.redis.pipeline()
            for event_type in self.VALID_EVENT_TYPES:
                key = f"safety:events:{event_type}"
                pipe.zcount(key, cutoff, "+inf")
            counts = pipe.execute()
            return sum(counts)
        except Exception as e:
            logger.error("total_event_count_error", error=str(e))
            return 0
