"""In-session context manager for memoization."""

import hashlib
import json
import structlog

logger = structlog.get_logger()


class ContextManager:
    """In-memory context manager for within-session memoization."""

    def __init__(self):
        """Initialize context manager."""
        self.results = {}

    def store_tool_result(self, tool_name: str, input_hash: str,
                         result) -> None:
        """Store tool execution result.

        Args:
            tool_name: Name of the tool
            input_hash: Hash of input (for memoization key)
            result: ToolResult object
        """
        key = f"{tool_name}:{input_hash}"
        self.results[key] = result
        logger.info("tool_result_stored", tool=tool_name, key=key)

    def get_tool_result(self, tool_name: str, input_hash: str):
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
