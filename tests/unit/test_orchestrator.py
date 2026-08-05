"""Unit tests for agent orchestration and tool failure handling."""

from unittest.mock import Mock, patch

import pytest

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


class SuccessfulResultTool:
    """Test double that returns a successful tool result."""

    name = "successful_result_tool"

    def execute(self, tool_input: dict) -> ToolResult:
        return ToolResult(success=True, data={"value": "result"})


class RaisingTool:
    """Test double that raises every time it is executed."""

    name = "raising_tool"

    def __init__(self) -> None:
        self.execute = Mock(side_effect=RuntimeError("forced tool exception"))


def test_run_logs_successful_and_failed_tool_results_separately() -> None:
    """ToolResult.success should select the appropriate execution log."""
    successful_tool = SuccessfulResultTool()
    failed_tool = FailedResultTool()
    orchestrator = Orchestrator(
        tools={
            successful_tool.name: successful_tool,
            failed_tool.name: failed_tool,
        }
    )

    with (
        patch.object(
            orchestrator,
            "_build_plan",
            return_value=[
                (successful_tool.name, {"test": True}),
                (failed_tool.name, {"test": True}),
            ],
        ),
        patch("agent.orchestrator.logger") as mock_logger,
    ):
        orchestrator.run(profile_id="test-profile", profile_data={})

    successful_execution_logs = [
        call.kwargs
        for call in mock_logger.info.call_args_list
        if call.args and call.args[0] == "tool_executed"
    ]
    failed_execution_logs = [
        call.kwargs
        for call in mock_logger.error.call_args_list
        if call.args and call.args[0] == "tool_execution_failed"
    ]
    assert successful_execution_logs == [
        {"tool": successful_tool.name, "success": True}
    ]
    assert failed_execution_logs == [
        {"tool": failed_tool.name, "error": "forced tool failure"}
    ]


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
    mock_logger.error.assert_any_call(
        "tool_execution_failed",
        tool=tool.name,
        error="forced tool failure",
    )


def test_run_retries_then_surfaces_exhausted_exception() -> None:
    """An exhausted tool exception should be logged and re-raised by run()."""
    tool = RaisingTool()
    orchestrator = Orchestrator(tools={tool.name: tool})

    with (
        patch.object(
            orchestrator,
            "_build_plan",
            return_value=[(tool.name, {"test": True})],
        ),
        patch("agent.error_handling.time.sleep"),
        patch("agent.orchestrator.logger") as mock_logger,
        pytest.raises(RuntimeError, match="forced tool exception"),
    ):
        orchestrator.run(profile_id="test-profile", profile_data={})

    assert tool.execute.call_count == 2
    mock_logger.error.assert_any_call(
        "tool_execution_failed",
        tool=tool.name,
        error="forced tool exception",
    )


def test_execute_tool_does_not_cache_failed_result() -> None:
    """A failed ToolResult should be executed again for the same input."""
    tool = FailedResultTool()
    orchestrator = Orchestrator(tools={tool.name: tool})
    tool_input = {"test": True}

    with patch.object(tool, "execute", wraps=tool.execute) as mock_execute:
        first_result = orchestrator._execute_tool(tool.name, tool_input)
        second_result = orchestrator._execute_tool(tool.name, tool_input)

    assert first_result.success is False
    assert second_result.success is False
    assert mock_execute.call_count == 2
    assert orchestrator.context_manager.get_all_results() == {}


def test_execute_tool_caches_successful_result() -> None:
    """A successful ToolResult should be reused for the same input."""
    tool = SuccessfulResultTool()
    orchestrator = Orchestrator(tools={tool.name: tool})
    tool_input = {"test": True}

    with patch.object(tool, "execute", wraps=tool.execute) as mock_execute:
        first_result = orchestrator._execute_tool(tool.name, tool_input)
        second_result = orchestrator._execute_tool(tool.name, tool_input)

    assert second_result is first_result
    assert mock_execute.call_count == 1
    assert list(orchestrator.context_manager.get_all_results().values()) == [first_result]
