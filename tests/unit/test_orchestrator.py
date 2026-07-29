"""Tests for orchestrator.py"""

from typing import Any

import pytest

from agent.orchestrator import Orchestrator


class SucceedingTool:
    """A tool that always succeeds."""

    name = "succeeding_tool"

    def execute(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok"}


class FailingTool:
    """A tool that always raises an exception."""

    name = "failing_tool"

    def execute(self, tool_input: dict[str, Any]) -> Any:
        raise ValueError("Simulated tool failure")


def make_plan(tool_names: list[str]):
    """Build a fake _build_plan function that schedules the given tools."""

    def _plan(profile_data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        return [(name, {}) for name in tool_names]

    return _plan


@pytest.mark.unit
class TestOrchestratorFailureSurfacing:
    """Test suite for orchestrator top-level failure surfacing (issue #44)."""

    def test_all_tools_succeed_no_errors_surfaced(self, monkeypatch):
        """When every tool succeeds, has_errors is False and failed_tools is empty."""
        orchestrator = Orchestrator(tools={"succeeding_tool": SucceedingTool()})
        monkeypatch.setattr(orchestrator, "_build_plan", make_plan(["succeeding_tool"]))

        result = orchestrator.run(profile_id="p1", profile_data={})

        assert result["has_errors"] is False
        assert result["failed_tools"] == []

    def test_one_tool_fails_is_surfaced(self, monkeypatch):
        """When one tool fails, has_errors is True and failed_tools names it."""
        orchestrator = Orchestrator(tools={
            "succeeding_tool": SucceedingTool(),
            "failing_tool": FailingTool(),
        })
        monkeypatch.setattr(
            orchestrator, "_build_plan", make_plan(["succeeding_tool", "failing_tool"])
        )

        result = orchestrator.run(profile_id="p1", profile_data={})

        assert result["has_errors"] is True
        assert result["failed_tools"] == ["failing_tool"]
        assert result["tool_results"]["failing_tool"]["success"] is False
        assert result["tool_results"]["succeeding_tool"] == {"status": "ok"}

    def test_all_tools_fail_all_are_surfaced(self, monkeypatch):
        """When every tool fails, has_errors is True and all names appear."""
        orchestrator = Orchestrator(tools={"failing_tool": FailingTool()})
        monkeypatch.setattr(orchestrator, "_build_plan", make_plan(["failing_tool"]))

        result = orchestrator.run(profile_id="p1", profile_data={})

        assert result["has_errors"] is True
        assert result["failed_tools"] == ["failing_tool"]

    def test_empty_plan_has_no_errors(self):
        """When profile_data yields an empty plan, has_errors is False."""
        orchestrator = Orchestrator(tools={})

        result = orchestrator.run(profile_id="p1", profile_data={})

        assert result["has_errors"] is False
        assert result["failed_tools"] == []
        assert result["tool_results"] == {}
