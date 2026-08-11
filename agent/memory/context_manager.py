"""In-session context manager for memoization."""

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any

import structlog

from ..tools.base import ToolResult
from .session_store import SessionStore

logger = structlog.get_logger()

# TTL for persisted in-progress context. Longer than the default session TTL
# so a long-running review can survive a restart plus recovery delay.
CONTEXT_TTL_SECONDS = 24 * 3600


class ContextManager:
    """Context manager for within-session memoization.

    Results are always cached in memory. When a session store and session id
    are provided, every stored result is also written through to Redis and
    reloaded on construction, so an in-progress session survives an API
    restart (issue #47).
    """

    def __init__(
        self,
        session_store: SessionStore | None = None,
        session_id: str | None = None,
    ):
        """Initialize context manager.

        Args:
            session_store: Optional SessionStore for write-through persistence
            session_id: Identifier scoping persisted results (e.g. profile id)
        """
        self.results: dict[str, Any] = {}
        self.session_store = session_store if session_id else None
        self.session_id = session_id
        if self.session_store:
            self._hydrate()

    def store_tool_result(self, tool_name: str, input_hash: str, result: Any) -> None:
        """Store tool execution result.

        Args:
            tool_name: Name of the tool
            input_hash: Hash of input (for memoization key)
            result: ToolResult object
        """
        key = f"{tool_name}:{input_hash}"
        self.results[key] = result
        logger.info("tool_result_stored", tool=tool_name, key=key)

        if self.session_store:
            self._persist()

    def get_tool_result(self, tool_name: str, input_hash: str) -> Any:
        """Get cached tool result.

        Args:
            tool_name: Name of the tool
            input_hash: Hash of input

        Returns:
            ToolResult or None if not found
        """
        key = f"{tool_name}:{input_hash}"
        result = self.results.get(key)

        if result:
            logger.info("tool_result_cache_hit", tool=tool_name, key=key)
        else:
            logger.info("tool_result_cache_miss", tool=tool_name, key=key)

        return result

    def get_all_results(self) -> dict:
        """Get all cached results.

        Returns:
            Dict of all cached results
        """
        return dict(self.results)

    def clear_persisted(self) -> None:
        """Delete persisted context once the session has completed."""
        if self.session_store:
            self.session_store.delete(self._store_key)

    @staticmethod
    def hash_input(input_data: dict) -> str:
        """Hash input data for consistent memoization.

        Args:
            input_data: Input dict

        Returns:
            SHA256 hash of input
        """
        json_str = json.dumps(input_data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    # ---- Persistence internals ----

    @property
    def _store_key(self) -> str:
        return f"{self.session_id}:context"

    def _hydrate(self) -> None:
        """Load previously persisted results into the in-memory cache."""
        if not self.session_store:
            return

        persisted = self.session_store.get(self._store_key)
        if not persisted:
            return

        # A key written by something other than this class (or a partially
        # written value) shouldn't take down startup — start cold instead.
        if not isinstance(persisted, dict):
            logger.warning(
                "context_hydrate_unexpected_payload",
                session_id=self.session_id,
                payload_type=type(persisted).__name__,
            )
            return

        for key, entry in persisted.items():
            self.results[key] = self._deserialize(entry)

        logger.info("context_hydrated", session_id=self.session_id, entries=len(self.results))

    def _persist(self) -> None:
        """Write the full cache through to the session store."""
        if not self.session_store:
            return

        serialized = {}
        for key, result in self.results.items():
            entry = self._serialize(result)
            if entry is not None:
                serialized[key] = entry

        self.session_store.set(self._store_key, serialized, ttl_seconds=CONTEXT_TTL_SECONDS)

    @staticmethod
    def _serialize(result: Any) -> dict | None:
        """Convert a cached result to a JSON-safe envelope, or None to skip."""
        # `is_dataclass` is true for the class itself as well as instances;
        # only an instance can go through `asdict`.
        if is_dataclass(result) and not isinstance(result, type):
            envelope = {"__kind__": "tool_result", "value": asdict(result)}
        else:
            envelope = {"__kind__": "raw", "value": result}

        try:
            json.dumps(envelope)
        except (TypeError, ValueError):
            logger.warning("context_result_not_serializable", result_type=type(result).__name__)
            return None

        return envelope

    @staticmethod
    def _deserialize(entry: Any) -> Any:
        """Rebuild a cached result from its persisted envelope."""
        if not isinstance(entry, dict) or "__kind__" not in entry:
            return entry

        value = entry.get("value")
        if entry["__kind__"] == "tool_result" and isinstance(value, dict):
            return ToolResult(
                success=value.get("success", False),
                data=value.get("data", {}),
                error=value.get("error"),
            )
        return value
