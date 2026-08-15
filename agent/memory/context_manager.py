"""In-session context manager for memoization."""

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any

import structlog

from agent.tools.base import ToolResult

logger = structlog.get_logger()


class ContextManager:
    """In-memory context manager for within-session memoization."""

    def __init__(self) -> None:
        """Initialize context manager."""
        self.results: dict[str, Any] = {}

    def store_tool_result(self, tool_name: str, input_hash: str, result: Any) -> None:
        """Store tool execution result.

        Args:
            tool_name: Name of the tool
            input_hash: Hash of input (for memoization key)
            result: Tool result to cache (typically a ``ToolResult``)
        """
        key = f"{tool_name}:{input_hash}"
        self.results[key] = result
        logger.info("tool_result_stored", tool=tool_name, key=key)

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

    def to_dict(self) -> dict[str, Any]:
        """Serialize cached results into a JSON-safe dict for persistence.

        Tool results are ``ToolResult`` dataclasses; these are converted to a
        tagged, JSON-serializable form so they can be stored in Redis and later
        restored via :meth:`from_dict`. Any result that cannot be serialized is
        skipped with a warning rather than raising, so a single bad entry never
        blocks persistence of the rest of the cache.

        Returns:
            Dict mapping cache keys to JSON-serializable payloads.
        """
        serialized: dict[str, Any] = {}
        for key, result in self.results.items():
            payload = self._serialize_result(result)
            if payload is None:
                logger.warning(
                    "context_result_not_serializable",
                    key=key,
                    result_type=type(result).__name__,
                )
                continue
            serialized[key] = payload
        return serialized

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore cached results from a persisted dict produced by :meth:`to_dict`.

        Entries are merged into the current cache. Malformed entries are skipped
        with a warning so a partially corrupt payload cannot wipe out an
        otherwise usable cache.

        Args:
            data: Dict of serialized cache payloads keyed by cache key.
        """
        if not data:
            return
        for key, payload in data.items():
            try:
                self.results[key] = self._deserialize_result(payload)
            except Exception as exc:  # noqa: BLE001 - graceful degradation
                logger.warning("context_result_restore_failed", key=key, error=str(exc))

    @staticmethod
    def _serialize_result(result: Any) -> dict[str, Any] | None:
        """Convert a single cached result into a JSON-safe payload.

        Returns None if the result cannot be safely serialized.
        """
        if is_dataclass(result) and not isinstance(result, type):
            return {
                "__kind__": "dataclass",
                "__class__": type(result).__name__,
                "value": asdict(result),
            }
        if isinstance(result, dict):
            try:
                json.dumps(result)
            except (TypeError, ValueError):
                return None
            return {"__kind__": "dict", "value": result}
        return None

    @staticmethod
    def _deserialize_result(payload: Any) -> Any:
        """Reconstruct a cached result from its serialized payload.

        Known ``ToolResult`` dataclasses are rebuilt as instances so cache hits
        keep the same interface (e.g. ``.data``) as freshly executed tools.
        Unknown dataclass types fall back to their raw value dict.
        """
        if isinstance(payload, dict) and payload.get("__kind__") == "dataclass":
            value = payload.get("value", {})
            if payload.get("__class__") == "ToolResult":
                return ToolResult(**value)
            return value
        if isinstance(payload, dict) and payload.get("__kind__") == "dict":
            return payload.get("value", {})
        return payload

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
