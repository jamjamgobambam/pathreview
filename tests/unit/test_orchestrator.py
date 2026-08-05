"""Tests for orchestrator state persistence and resume behavior."""

from unittest.mock import Mock

from agent.orchestrator import Orchestrator


class FakeTool:
    """Simple tool used in orchestrator tests."""

    def __init__(self, name: str, result: dict):
        self.name = name
        self.result = result
        self.execute_count = 0

    def execute(self, input_data: dict) -> dict:
        """Return the configured result and count executions."""
        self.execute_count += 1
        return self.result


class FixedPlanOrchestrator(Orchestrator):
    """Orchestrator with a fixed execution plan for tests."""

    def _build_plan(self, profile_data: dict) -> list[tuple[str, dict]]:
        """Return a deterministic two-tool plan."""
        return [
            ("first_tool", {"value": 1}),
            ("second_tool", {"value": 2}),
        ]


def test_checkpoints_after_each_successful_tool() -> None:
    """Each completed tool should be persisted immediately."""
    first_tool = FakeTool("first_tool", {"first": "complete"})
    second_tool = FakeTool("second_tool", {"second": "complete"})

    session_store = Mock()
    session_store.get.return_value = None

    orchestrator = FixedPlanOrchestrator(
        tools={
            "first_tool": first_tool,
            "second_tool": second_tool,
        },
        session_store=session_store,
    )

    result = orchestrator.run("profile-123", {})

    assert first_tool.execute_count == 1
    assert second_tool.execute_count == 1
    assert session_store.set.call_count == 2

    assert session_store.set.call_args_list[0].args == (
        "profile-123",
        {"first_tool": {"first": "complete"}},
    )

    assert session_store.set.call_args_list[1].args == (
        "profile-123",
        {
            "first_tool": {"first": "complete"},
            "second_tool": {"second": "complete"},
        },
    )

    assert result["tool_results"] == {
        "first_tool": {"first": "complete"},
        "second_tool": {"second": "complete"},
    }


def test_resumes_without_rerunning_completed_tool() -> None:
    """Previously completed tools should be restored and skipped."""
    first_tool = FakeTool("first_tool", {"new": "result"})
    second_tool = FakeTool("second_tool", {"second": "complete"})

    session_store = Mock()
    session_store.get.return_value = {
        "first_tool": {"first": "restored"},
    }

    orchestrator = FixedPlanOrchestrator(
        tools={
            "first_tool": first_tool,
            "second_tool": second_tool,
        },
        session_store=session_store,
    )

    result = orchestrator.run("profile-123", {})

    assert first_tool.execute_count == 0
    assert second_tool.execute_count == 1

    session_store.set.assert_called_once_with(
        "profile-123",
        {
            "first_tool": {"first": "restored"},
            "second_tool": {"second": "complete"},
        },
    )

    assert result["tool_results"] == {
        "first_tool": {"first": "restored"},
        "second_tool": {"second": "complete"},
    }


def test_runs_without_session_store() -> None:
    """The orchestrator should still work when persistence is disabled."""
    first_tool = FakeTool("first_tool", {"first": "complete"})
    second_tool = FakeTool("second_tool", {"second": "complete"})

    orchestrator = FixedPlanOrchestrator(
        tools={
            "first_tool": first_tool,
            "second_tool": second_tool,
        }
    )

    result = orchestrator.run("profile-123", {})

    assert first_tool.execute_count == 1
    assert second_tool.execute_count == 1

    assert result["tool_results"] == {
        "first_tool": {"first": "complete"},
        "second_tool": {"second": "complete"},
    }
