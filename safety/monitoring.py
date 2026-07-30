"""Safety event monitoring.

This module stores per-event-type occurrences in Redis sorted sets keyed by
`safety:events:<event_type>` using the event timestamp as the score. This
allows efficient rolling-window counts (e.g. last hour) using `ZCOUNT`.
"""

import time
import uuid
from datetime import datetime

import redis
import structlog

logger = structlog.get_logger()


class SafetyMonitor:
    """Monitor and log safety events using Redis sorted sets.

    Each event is added to a sorted set with the Unix timestamp (float seconds)
    as the score and a unique member value. Old entries are trimmed to a
    retention window (24 hours) to keep storage bounded.
    """

    # Valid event types
    VALID_EVENT_TYPES = {
        "pii_detected",
        "injection_attempt",
        "content_filtered",
        "bias_detected",
        "rate_limited",
    }

    # Retain events for this many seconds (24 hours)
    RETENTION_SECONDS = 86400

    def __init__(self, redis_client: redis.Redis):
        """Initialize safety monitor.

        Args:
            redis_client: Redis client
        """
        self.redis = redis_client

    def _key(self, event_type: str) -> str:
        return f"safety:events:{event_type}"

    def log_event(self, event_type: str, details: dict) -> None:
        """Log a safety event.

        Stores the event in a Redis sorted set with the current timestamp as the
        score so that rolling-window counts can be computed with `ZCOUNT`.
        """
        if event_type not in self.VALID_EVENT_TYPES:
            logger.warning("unknown_event_type", event_type=event_type)
            return

        iso_ts = datetime.utcnow().isoformat()
        ts = time.time()

        try:
            # Log to structlog for auditability
            logger.warning("safety_event", event_type=event_type, timestamp=iso_ts, **details)

            key = self._key(event_type)

            # Use a unique member value to allow duplicate timestamps
            member = f"{ts}:{uuid.uuid4().hex}"

            # Add to sorted set with timestamp score
            # redis-py expects a mapping of member->score
            self.redis.zadd(key, {member: ts})

            # Trim entries older than retention window
            max_allowed = ts - self.RETENTION_SECONDS
            if max_allowed > 0:
                try:
                    self.redis.zremrangebyscore(key, 0, max_allowed)
                except Exception:
                    # best-effort trimming; don't fail the whole logging
                    logger.debug("zremrangebyscore_failed", key=key)

            # Ensure the key expires after at most retention seconds
            try:
                self.redis.expire(key, self.RETENTION_SECONDS)
            except Exception:
                logger.debug("expire_failed", key=key)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def get_event_count(self, event_type: str, window_hours: int = 1) -> int:
        """Get count of safety events in a rolling window.

        Args:
            event_type: Type of event
            window_hours: Time window in hours to count

        Returns:
            Count of events in the window
        """
        key = self._key(event_type)
        now = time.time()
        window_seconds = int(window_hours * 3600)
        start = now - window_seconds

        try:
            # ZCOUNT min/max are inclusive; use start..now
            count = self.redis.zcount(key, start, now)
            return int(count) if count is not None else 0

        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0

    def get_total_event_count(self, window_hours: int = 1) -> int:
        """Return aggregate count across all event types for the window."""
        total = 0
        try:
            for et in self.VALID_EVENT_TYPES:
                total += self.get_event_count(et, window_hours=window_hours)
            return total
        except Exception as e:
            logger.error("total_event_count_error", error=str(e))
            return 0
