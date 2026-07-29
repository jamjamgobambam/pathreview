"""Unit tests for agent orchestration and tool failure handling."""

from unittest.mock import Mock, patch

from agent.orchestrator import Orchestrator
from agent.tools.base import ToolResult


class FailedResultTool:
    """Test double that reports a failure without raising an exception."""

    name = "failed_result_tool"

    def execute(self, tool_input: dict) -> ToolResult:
        return ToolResult(
            success=False,
            data={},
            error="forced tool failure",
        )


class RaisingTool:
    """Test double that raises every time it is executed."""

    name = "raising_tool"

    def __init__(self) -> None:
        self.execute = Mock(side_effect=RuntimeError("forced tool exception"))


def test_run_preserves_failed_tool_result_and_does_not_log_success() -> None:
    """A failed ToolResult should remain visible in the orchestrator response."""
    tool = FailedResultTool()
    orchestrator = Orchestrator(tools={tool.name: tool})

    with (
        patch.object(
            orchestrator,
            "_build_plan",
            return_value=[(tool.name, {"test": True})],
        ),
        patch("agent.orchestrator.logger") as mock_logger,
    ):
        result = orchestrator.run(profile_id="test-profile", profile_data={})

    assert result["tool_results"][tool.name] == {
        "success": False,
        "error": "forced tool failure",
    }
    assert not any(
        call.kwargs.get("tool") == tool.name and call.kwargs.get("success") is True
        for call in mock_logger.info.call_args_list
    )


def test_run_retries_raised_exception_then_returns_error_result() -> None:
    """A raised tool error is retried, then converted to an error by run()."""
    tool = RaisingTool()
    orchestrator = Orchestrator(tools={tool.name: tool})

    with (
        patch.object(
            orchestrator,
            "_build_plan",
            return_value=[(tool.name, {"test": True})],
        ),
        patch("agent.error_handling.time.sleep"),
    ):
        result = orchestrator.run(profile_id="test-profile", profile_data={})

    assert tool.execute.call_count == 2
    assert result["tool_results"][tool.name] == {
        "error": "forced tool exception",
        "success": False,
    }
