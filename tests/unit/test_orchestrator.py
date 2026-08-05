"""Tests for orchestrator.py

Covers the fix for issue #44: the plan-execute loop in `Orchestrator.run()`
used to wrap each tool call in a broad `except Exception` and silently
continue, producing a `tool_results` entry with a different shape than a
successful one and no run-level indication that anything failed.
"""

import pytest

from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult
from agent.tools.tech_detector import TechDetector


class AlwaysFailsTool(BaseTool):
    """Simulates a tool whose upstream dependency (e.g. GitHub API) fails."""

    name = "readme_scorer"
    description = "Intentionally broken tool for testing failure handling"

    def execute(self, input_data: dict) -> ToolResult:
        raise RuntimeError("simulated upstream API failure (e.g. GitHub 500)")


class AlwaysTimesOutTool(BaseTool):
    """Simulates a tool that times out rather than raising a normal error."""

    name = "skill_extractor"
    description = "Intentionally times out for testing failure handling"

    def execute(self, input_data: dict) -> ToolResult:
        raise TimeoutError("simulated timeout")


@pytest.mark.unit
class TestOrchestratorToolFailureHandling:
    """Tests that a failing tool is surfaced instead of silently swallowed."""

    def test_run_does_not_raise_when_a_tool_fails(self):
        """`run()` completes normally even though a tool raised every retry."""
        orchestrator = Orchestrator(
            tools={
                "tech_detector": TechDetector(),
                "readme_scorer": AlwaysFailsTool(),
            }
        )

        output = orchestrator.run(
            profile_id="profile-123",
            profile_data={
                "files": ["main.py", "package.json"],
                "readme_content": "# My Project",
            },
        )

        assert output["profile_id"] == "profile-123"

    def test_failed_tool_reported_with_run_level_signal(self):
        """A failed tool is reported both in `failed_tools` and via `status`,
        and its `tool_results` entry has the same shape as a successful one.
        """
        orchestrator = Orchestrator(
            tools={
                "tech_detector": TechDetector(),
                "readme_scorer": AlwaysFailsTool(),
            }
        )

        output = orchestrator.run(
            profile_id="profile-123",
            profile_data={
                "files": ["main.py"],
                "readme_content": "# My Project",
            },
        )

        assert output["status"] == "partial"
        assert output["failed_tools"] == ["readme_scorer"]

        failed_result = output["tool_results"]["readme_scorer"]
        succeeded_result = output["tool_results"]["tech_detector"]

        assert failed_result == {
            "success": False,
            "data": None,
            "error": "simulated upstream API failure (e.g. GitHub 500)",
        }
        assert succeeded_result["success"] is True
        assert succeeded_result["error"] is None
        assert succeeded_result["data"]["primary_language"] == "Python"

    def test_all_tools_succeed_reports_complete_status(self):
        """No regression: an all-success run reports status="complete" with
        no failed tools."""
        orchestrator = Orchestrator(tools={"tech_detector": TechDetector()})

        output = orchestrator.run(
            profile_id="profile-789",
            profile_data={"files": ["main.py"]},
        )

        assert output["status"] == "complete"
        assert output["failed_tools"] == []
        assert output["tool_results"]["tech_detector"]["success"] is True

    def test_all_tools_fail_reports_failed_status(self):
        """When every planned tool fails, status is "failed", not "partial"."""
        orchestrator = Orchestrator(
            tools={
                "readme_scorer": AlwaysFailsTool(),
            }
        )

        output = orchestrator.run(
            profile_id="profile-999",
            profile_data={"readme_content": "# My Project"},
        )

        assert output["status"] == "failed"
        assert output["failed_tools"] == ["readme_scorer"]

    def test_timeout_reported_with_same_shape_as_other_failures(self):
        """A `TimeoutError` is reported the same way as any other failure."""
        orchestrator = Orchestrator(
            tools={
                "skill_extractor": AlwaysTimesOutTool(),
            }
        )

        output = orchestrator.run(
            profile_id="profile-timeout",
            profile_data={"resume_text": "some resume text"},
        )

        assert output["status"] == "failed"
        assert output["failed_tools"] == ["skill_extractor"]
        assert output["tool_results"]["skill_extractor"]["success"] is False
        assert "simulated timeout" in output["tool_results"]["skill_extractor"]["error"]

    def test_no_session_store_does_not_affect_failure_reporting(self):
        """Failure reporting doesn't depend on a session_store being configured."""
        orchestrator = Orchestrator(
            tools={"readme_scorer": AlwaysFailsTool()},
            session_store=None,
        )

        output = orchestrator.run(
            profile_id="profile-no-session",
            profile_data={"readme_content": "# My Project"},
        )

        assert output["status"] == "failed"
        assert output["failed_tools"] == ["readme_scorer"]


@pytest.mark.unit
class TestOrchestratorUnregisteredToolHandling:
    """Tests for `_build_plan` skipping tools that aren't registered."""

    def test_plan_skips_unregistered_market_analyzer_tool(self):
        """`_build_plan` used to always append `market_analyzer` whenever any
        other tool ran, even if it wasn't registered in `self.tools`, which
        hit the exact same silent-failure path via an "Unknown tool" error.
        It should now be skipped instead of queued to fail.
        """
        orchestrator = Orchestrator(tools={"tech_detector": TechDetector()})

        output = orchestrator.run(
            profile_id="profile-456",
            profile_data={"files": ["main.py"]},
        )

        assert "market_analyzer" not in output["tool_results"]
        assert output["status"] == "complete"
        assert output["failed_tools"] == []

    def test_unregistered_tool_and_execution_failure_are_reported_the_same_way(self):
        """A tool that's registered but fails at execution time should be
        reported identically to one that was never queued because it wasn't
        registered -- both surface as a run-level failure signal, not a
        result with a different shape mixed into `tool_results`.
        """
        orchestrator_missing_tool = Orchestrator(tools={"tech_detector": TechDetector()})
        orchestrator_failing_tool = Orchestrator(
            tools={
                "tech_detector": TechDetector(),
                "market_analyzer": AlwaysFailsTool(),
            }
        )

        output_missing = orchestrator_missing_tool.run(
            profile_id="profile-a",
            profile_data={"files": ["main.py"]},
        )
        output_failing = orchestrator_failing_tool.run(
            profile_id="profile-b",
            profile_data={"files": ["main.py"]},
        )

        # Unregistered tool: silently skipped, run is still "complete".
        assert output_missing["status"] == "complete"
        assert "market_analyzer" not in output_missing["tool_results"]

        # Registered but failing tool: reported via the uniform failure shape.
        assert output_failing["status"] == "partial"
        assert output_failing["tool_results"]["market_analyzer"]["success"] is False
