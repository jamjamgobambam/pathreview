"""Redis-backed session store."""

import redis
import json
import structlog
from typing import Optional

logger = structlog.get_logger()


class SessionStore:
    """Store and retrieve session data from Redis."""

    def __init__(self, redis_client: redis.Redis):
        """Initialize session store.

        Args:
            redis_client: Redis client
        """
        self.redis = redis_client

    def get(self, session_id: str) -> Optional[dict]:
        """Get session data.

        Args:
            session_id: Session identifier

        Returns:
            Session dict or None if expired/not found
        """
        key = f"session:{session_id}"

        try:
            data = self.redis.get(key)
            if not data:
                logger.info("session_not_found", session_id=session_id)
                return None

            parsed = json.loads(data)
            logger.info("session_retrieved", session_id=session_id)
            return parsed

        except json.JSONDecodeError:
            logger.error("session_decode_error", session_id=session_id)
            return None
        except Exception as e:
            logger.error("session_get_error", session_id=session_id, error=str(e))
            return None

    def set(self, session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
        """Store session data.

        Args:
            session_id: Session identifier
            data: Session data dict
            ttl_seconds: Time to live in seconds (default 1 hour)
        """
        key = f"session:{session_id}"

        try:
            json_data = json.dumps(data)
            self.redis.setex(key, ttl_seconds, json_data)
            logger.info("session_stored", session_id=session_id, ttl_seconds=ttl_seconds)

        except Exception as e:
            logger.error("session_set_error", session_id=session_id, error=str(e))

    def delete(self, session_id: str) -> None:
        """Delete session data.

        Args:
            session_id: Session identifier
        """
        key = f"session:{session_id}"

        try:
            self.redis.delete(key)
            logger.info("session_deleted", session_id=session_id)

        except Exception as e:
            logger.error("session_delete_error", session_id=session_id, error=str(e))
