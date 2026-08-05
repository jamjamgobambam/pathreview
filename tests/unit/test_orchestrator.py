"""Tests for orchestrator.py"""

import pytest

from agent.memory.context_manager import ContextManager
from agent.orchestrator import Orchestrator


class CountingTool:
    """Fake tool that tracks how many times it was actually executed."""

    name = "tech_detector"

    def __init__(self) -> None:
        self.call_count = 0

    def execute(self, tool_input: dict) -> dict:
        self.call_count += 1
        return {"call_number": self.call_count}


@pytest.mark.unit
class TestOrchestrator:
    """Test suite for Orchestrator."""

    @pytest.fixture
    def tool(self) -> CountingTool:
        """Create a fake tool that counts real executions."""
        return CountingTool()

    @pytest.fixture
    def orchestrator(self, tool: CountingTool) -> Orchestrator:
        """Create an Orchestrator wired up with the fake tool."""
        return Orchestrator(tools={"tech_detector": tool}, session_store=None)

    def test_second_review_reexecutes_tools(
        self, orchestrator: Orchestrator, tool: CountingTool
    ) -> None:
        """A second review for the same profile must not reuse a previous
        review's cached tool result (issue #43)."""
        profile_id = "profile-123"
        profile_data = {"files": ["main.py"]}

        orchestrator.run(profile_id, profile_data)
        orchestrator.run(profile_id, profile_data)

        assert tool.call_count == 2

    def test_different_profiles_do_not_share_cache(
        self, orchestrator: Orchestrator, tool: CountingTool
    ) -> None:
        """Reviewing two different profiles must not share cached results."""
        profile_data = {"files": ["main.py"]}

        orchestrator.run("profile-a", profile_data)
        orchestrator.run("profile-b", profile_data)

        assert tool.call_count == 2

    def test_memoizes_within_a_single_review(
        self, orchestrator: Orchestrator, tool: CountingTool
    ) -> None:
        """Within one review (same ContextManager), repeated calls for the
        same tool+input should still be memoized."""
        context_manager = ContextManager()
        tool_input = {"files": ["main.py"]}

        orchestrator._execute_tool("tech_detector", tool_input, context_manager)
        orchestrator._execute_tool("tech_detector", tool_input, context_manager)

        assert tool.call_count == 1

    def test_run_returns_tool_results(self, orchestrator: Orchestrator) -> None:
        """run() should return the tool's result under tool_results."""
        result = orchestrator.run("profile-123", {"files": ["main.py"]})

        assert "tool_results" in result
        assert "tech_detector" in result["tool_results"]

    def test_unknown_tool_in_plan_is_handled_gracefully(self) -> None:
        """A planned tool with no matching entry in `tools` should be
        recorded as a failed result, not raise or crash the whole review."""
        orchestrator = Orchestrator(tools={}, session_store=None)

        result = orchestrator.run("profile-123", {"files": ["main.py"]})

        assert result["tool_results"]["tech_detector"]["success"] is False