"""Tests for orchestrator session state boundaries."""

from typing import Any, cast

import pytest

from agent.orchestrator import Orchestrator
from agent.tools.base import ToolResult


class FakeSessionStore:
    """Simple in-memory replacement for the Redis session store."""

    def __init__(self) -> None:
        self.data: dict[str, dict[str, Any]] = {}

    def get(self, session_id: str) -> dict[str, Any] | None:
        """Return saved session data."""
        return self.data.get(session_id)

    def set(self, session_id: str, data: dict[str, Any], ttl_seconds: int = 3600) -> None:
        """Save session data."""
        self.data[session_id] = dict(data)


class CountingTool:
    """Tool that records how many times it was executed."""

    name = "readme_scorer"

    def __init__(self) -> None:
        self.call_count = 0

    def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Return the README content and increment the call count."""
        self.call_count += 1
        return ToolResult(
            success=True,
            data={
                "call_count": self.call_count,
                "readme_content": input_data["readme_content"],
            },
        )


class FakeMarketAnalyzer:
    """Fake market analyzer used because the orchestrator appends it to plans."""

    name = "market_analyzer"

    def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Return a simple successful market analysis result."""
        return ToolResult(success=True, data={"ran": True})


@pytest.mark.unit
class TestOrchestratorSessionState:
    """Test suite for persisted orchestrator session state."""

    def test_second_review_does_not_keep_stale_tool_results(self) -> None:
        """Test each review stores only the tools that ran for that review."""
        session_store = FakeSessionStore()
        readme_scorer = CountingTool()
        orchestrator = Orchestrator(
            tools={
                "market_analyzer": FakeMarketAnalyzer(),
                "readme_scorer": readme_scorer,
            },
            session_store=cast("Any", session_store),
        )

        first_result = orchestrator.run(
            profile_id="same-profile",
            profile_data={"readme_content": "README 1"},
        )
        second_result = orchestrator.run(
            profile_id="same-profile",
            profile_data={},
        )

        assert sorted(first_result["tool_results"]) == [
            "market_analyzer",
            "readme_scorer",
        ]
        assert second_result["tool_results"] == {}
        assert session_store.data["same-profile"] == {}

    def test_same_tool_input_is_recomputed_for_new_review(self) -> None:
        """Test memoized tool output does not leak into the next review."""
        readme_scorer = CountingTool()
        orchestrator = Orchestrator(
            tools={
                "market_analyzer": FakeMarketAnalyzer(),
                "readme_scorer": readme_scorer,
            }
        )

        first_result = orchestrator.run(
            profile_id="same-profile",
            profile_data={"readme_content": "README 1"},
        )
        second_result = orchestrator.run(
            profile_id="same-profile",
            profile_data={"readme_content": "README 1"},
        )

        assert first_result["tool_results"]["readme_scorer"]["call_count"] == 1
        assert second_result["tool_results"]["readme_scorer"]["call_count"] == 2
