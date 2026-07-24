"""Tests for orchestrator.py

Reproduction for issue #44: "Orchestrator catches all exceptions from tool
calls and continues without logging the failure."

Every tool in agent/tools/ (github_tool.py, tech_detector.py,
readme_scorer.py, skill_extractor.py, market_analyzer.py) catches its own
exceptions internally inside execute() and always returns a ToolResult --
success=True or success=False -- rather than letting an exception propagate.
Orchestrator.run() (agent/orchestrator.py) never inspects `result.success` or
`result.error`; it unconditionally does `results[tool_name] = result.data`
and logs `tool_executed ... success=True`, regardless of what the tool
actually reported.

The test below encodes the expected, correct behavior: when a tool reports
failure, the orchestrator should log that failure and the failure should be
visible in the returned results, not silently collapsed into an empty dict
tagged as a success. It fails against the current implementation.
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


@pytest.mark.unit
class TestOrchestratorToolFailureLogging:
    """Reproduction test for issue #44."""

    def test_run_logs_and_preserves_failed_tool_result(self, monkeypatch):
        """When a tool reports failure, run() should log it at error level
        and preserve the failure in the returned tool_results, instead of
        silently storing an empty dict and logging a false success.
        """
        spy = SpyLogger()
        monkeypatch.setattr("agent.orchestrator.logger", spy)

        orchestrator = Orchestrator(tools={"tech_detector": FailingTool()})
        # Bypass _build_plan (its own logic is unrelated to this issue) so
        # the test isolates exactly the result-handling defect in run().
        monkeypatch.setattr(
            orchestrator,
            "_build_plan",
            lambda profile_data: [("tech_detector", {"files": ["main.py"]})],
        )

        output = orchestrator.run("profile-1", {"files": ["main.py"]})

        assert spy.calls_at_level("error"), (
            "expected an error-level log when a tool reports failure, "
            f"but only these calls were logged: {spy.calls}"
        )

        tech_result = output["tool_results"]["tech_detector"]
        assert isinstance(tech_result, dict)
        assert tech_result.get("success") is False, (
            "expected the failure to be visible in tool_results, but got "
            f"{tech_result!r} -- indistinguishable from an empty success"
        )
        assert "error" in tech_result
