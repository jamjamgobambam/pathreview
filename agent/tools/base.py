"""Base tool interface."""

from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    data: dict
    error: str | None = None


class BaseTool(ABC):
    """Base class for all tools."""

    name: str
    description: str

    @abstractmethod
    def execute(self, input_data: dict) -> ToolResult:
        """Execute the tool.

        Args:
            input_data: Input parameters

        Returns:
            ToolResult with success status and data
        """
        pass
