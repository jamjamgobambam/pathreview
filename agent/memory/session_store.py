"""Redis-backed session store."""

import json

import redis
import structlog

logger = structlog.get_logger()


class SessionStore:
    """Store and retrieve session data from Redis."""

    def __init__(self, redis_client: redis.Redis):
        """Initialize session store.

        Args:
            redis_client: Redis client
        """
        self.redis = redis_client

    def get(self, session_id: str) -> dict | None:
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

            parsed: dict = json.loads(data)
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

    def get_cache(self, session_id: str) -> dict | None:
        """Get the persisted agent context cache for a session.

        The context cache holds memoized tool results (see
        :class:`~agent.memory.context_manager.ContextManager`). It is stored
        under a separate ``cache:`` key so it can be restored independently of
        the session's tool output state after an API restart.

        Args:
            session_id: Session identifier

        Returns:
            Cache dict or None if expired/not found.
        """
        key = f"cache:{session_id}"

        try:
            data = self.redis.get(key)
            if not data:
                logger.info("cache_not_found", session_id=session_id)
                return None

            parsed: dict = json.loads(data)
            logger.info("cache_retrieved", session_id=session_id)
            return parsed

        except json.JSONDecodeError:
            logger.error("cache_decode_error", session_id=session_id)
            return None
        except Exception as e:
            logger.error("cache_get_error", session_id=session_id, error=str(e))
            return None

    def set_cache(self, session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
        """Persist the agent context cache for a session.

        Serialized tool results are stored under a ``cache:`` key with a TTL so
        that an in-progress review can resume its memoized work after the API
        process restarts. Failures are logged but never raised, so persistence
        problems degrade gracefully to in-memory-only behavior.

        Args:
            session_id: Session identifier
            data: Serialized context cache (from ``ContextManager.to_dict()``)
            ttl_seconds: Time to live in seconds (default 1 hour)
        """
        key = f"cache:{session_id}"

        try:
            json_data = json.dumps(data)
            self.redis.setex(key, ttl_seconds, json_data)
            logger.info("cache_stored", session_id=session_id, ttl_seconds=ttl_seconds)

        except Exception as e:
            logger.error("cache_set_error", session_id=session_id, error=str(e))
