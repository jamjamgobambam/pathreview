"""Tests for orchestrator.py

Covers issue #44: "Orchestrator catches all exceptions from tool calls and
continues without logging the failure."

Every tool in agent/tools/ (github_tool.py, tech_detector.py,
readme_scorer.py, skill_extractor.py, market_analyzer.py) catches its own
exceptions internally inside execute() and always returns a ToolResult --
success=True or success=False -- rather than letting an exception propagate.
Orchestrator.run() and Orchestrator._execute_tool() now inspect
`result.success` before deciding what to log, what to store in
`tool_results`, and what to cache -- see agent/orchestrator.py.
"""

import pytest

from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult


class FailingTool(BaseTool):
    """A tool that fails the way every real tool in this repo fails: by
    catching its own exception internally and returning
    ToolResult(success=False, ...) rather than raising."""

    name = "tech_detector"
    description = "Simulates a tool that fails internally without raising"

    def execute(self, input_data: dict) -> ToolResult:
        return ToolResult(success=False, data={}, error="simulated tool failure")


class CountingFailingTool(BaseTool):
    """Like FailingTool, but tracks how many times execute() was called, so
    tests can assert on whether a failure was cached."""

    name = "tech_detector"
    description = "Simulates a tool that fails internally, counting calls"

    def __init__(self):
        self.call_count = 0

    def execute(self, input_data: dict) -> ToolResult:
        self.call_count += 1
        return ToolResult(success=False, data={}, error="simulated tool failure")


class CountingSucceedingTool(BaseTool):
    """A tool that succeeds and tracks how many times execute() was called,
    so tests can assert that successful results are still cached."""

    name = "tech_detector"
    description = "Simulates a tool that succeeds, counting calls"

    def __init__(self):
        self.call_count = 0

    def execute(self, input_data: dict) -> ToolResult:
        self.call_count += 1
        return ToolResult(success=True, data={"primary_language": "Python"})


class RaisingTool(BaseTool):
    """A tool that raises directly instead of returning
    ToolResult(success=False). Not how any current tool behaves, but the
    orchestrator must handle it consistently with the ToolResult-based
    failure path."""

    name = "tech_detector"
    description = "Simulates a tool that raises instead of returning a result"

    def execute(self, input_data: dict) -> ToolResult:
        raise RuntimeError("boom")


class SpyLogger:
    """Records structlog-style calls so we can assert on what was logged."""

    def __init__(self):
        self.calls = []

    def info(self, event, **kwargs):
        self.calls.append(("info", event, kwargs))

    def warning(self, event, **kwargs):
        self.calls.append(("warning", event, kwargs))

    def error(self, event, **kwargs):
        self.calls.append(("error", event, kwargs))

    def calls_at_level(self, level):
        return [c for c in self.calls if c[0] == level]


def _run_single_tool(monkeypatch, tool, tool_name="tech_detector"):
    """Run Orchestrator.run() with a single tool in the plan, bypassing
    _build_plan (its own logic is unrelated to this issue) so each test
    isolates exactly the result-handling behavior in run()."""
    spy = SpyLogger()
    monkeypatch.setattr("agent.orchestrator.logger", spy)

    orchestrator = Orchestrator(tools={tool_name: tool})
    monkeypatch.setattr(
        orchestrator,
        "_build_plan",
        lambda profile_data: [(tool_name, {"files": ["main.py"]})],
    )

    output = orchestrator.run("profile-1", {"files": ["main.py"]})
    return output, spy


@pytest.mark.unit
class TestOrchestratorToolFailureLogging:
    """Reproduction and regression tests for issue #44."""

    def test_run_logs_and_preserves_failed_tool_result(self, monkeypatch):
        """When a tool reports failure via ToolResult(success=False), run()
        must log it at error level and preserve the failure in the returned
        tool_results, instead of silently storing an empty dict and logging
        a false success."""
        output, spy = _run_single_tool(monkeypatch, FailingTool())

        assert spy.calls_at_level("error"), (
            "expected an error-level log when a tool reports failure, "
            f"but only these calls were logged: {spy.calls}"
        )

        tech_result = output["tool_results"]["tech_detector"]
        assert isinstance(tech_result, dict)
        assert tech_result.get("success") is False
        assert tech_result.get("error") == "simulated tool failure"

        # No misleading success log for the failed tool.
        false_success = [
            c
            for c in spy.calls_at_level("info")
            if c[1] == "tool_executed" and c[2].get("success") is True
        ]
        assert not false_success

    def test_run_success_path_is_unchanged(self, monkeypatch):
        """A successful tool call must still log success=True and store the
        tool's bare data dict in tool_results (no regression)."""
        output, spy = _run_single_tool(monkeypatch, CountingSucceedingTool())

        assert output["tool_results"]["tech_detector"] == {"primary_language": "Python"}

        success_logs = [
            c
            for c in spy.calls_at_level("info")
            if c[1] == "tool_executed" and c[2].get("success") is True
        ]
        assert success_logs
        assert not spy.calls_at_level("error")

    def test_run_handles_raised_exception_consistently_with_failed_result(self, monkeypatch):
        """A tool that raises directly (instead of returning
        ToolResult(success=False)) must produce the same failure shape as
        the ToolResult-based failure path, not a different format."""
        output, spy = _run_single_tool(monkeypatch, RaisingTool())

        assert spy.calls_at_level("error")

        tech_result = output["tool_results"]["tech_detector"]
        assert tech_result == {"error": "boom", "success": False}

    def test_run_logs_error_for_unknown_tool(self, monkeypatch):
        """Pre-existing correct behavior: a plan step referencing a tool name
        that isn't registered must still log an error and record the
        failure, unchanged by this fix."""
        spy = SpyLogger()
        monkeypatch.setattr("agent.orchestrator.logger", spy)

        orchestrator = Orchestrator(tools={})
        monkeypatch.setattr(
            orchestrator,
            "_build_plan",
            lambda profile_data: [("nonexistent_tool", {})],
        )

        output = orchestrator.run("profile-1", {})

        assert spy.calls_at_level("error")
        result = output["tool_results"]["nonexistent_tool"]
        assert result["success"] is False
        assert "Unknown tool" in result["error"]

    def test_run_reflects_each_tool_outcome_independently(self, monkeypatch):
        """When multiple tools run in the same plan, a failure in one must
        not affect another tool's own recorded outcome."""
        spy = SpyLogger()
        monkeypatch.setattr("agent.orchestrator.logger", spy)

        orchestrator = Orchestrator(
            tools={
                "tech_detector": FailingTool(),
                "readme_scorer": CountingSucceedingTool(),
            }
        )
        monkeypatch.setattr(
            orchestrator,
            "_build_plan",
            lambda profile_data: [
                ("tech_detector", {}),
                ("readme_scorer", {}),
            ],
        )

        output = orchestrator.run("profile-1", {})

        assert output["tool_results"]["tech_detector"] == {
            "error": "simulated tool failure",
            "success": False,
        }
        assert output["tool_results"]["readme_scorer"] == {"primary_language": "Python"}


@pytest.mark.unit
class TestOrchestratorFailureCaching:
    """A failed tool result must not be cached -- caching it would replay the
    same failure as a "cache hit" on a later call within the same session,
    silently skipping any retry."""

    def test_failed_result_is_not_cached(self):
        tool = CountingFailingTool()
        orchestrator = Orchestrator(tools={"tech_detector": tool})

        first = orchestrator._execute_tool("tech_detector", {"files": ["main.py"]})
        second = orchestrator._execute_tool("tech_detector", {"files": ["main.py"]})

        assert first.success is False
        assert second.success is False
        assert tool.call_count == 2, (
            "expected the tool to be re-executed on the second call, but "
            "the failed result appears to have been served from cache"
        )

    def test_successful_result_is_still_cached(self):
        """Regression check: the caching fix must not disable memoization
        for successful results."""
        tool = CountingSucceedingTool()
        orchestrator = Orchestrator(tools={"tech_detector": tool})

        orchestrator._execute_tool("tech_detector", {"files": ["main.py"]})
        orchestrator._execute_tool("tech_detector", {"files": ["main.py"]})

        assert tool.call_count == 1, "expected the second call to be served from cache"
