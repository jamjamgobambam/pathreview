from unittest.mock import Mock

from agent.orchestrator import Orchestrator


class TestOrchestratorFailureHandling:

    def test_run_does_not_signal_partial_failure_at_top_level(self) -> None:
        """Reproduces issue #44: a failing tool is buried in results
        with no top-level indicator that the review is incomplete."""
        failing_tool = Mock()
        failing_tool.execute.side_effect = Exception("tool crashed")

        orchestrator = Orchestrator(tools={"tech_detector": failing_tool})
        result = orchestrator.run(profile_id="test-1", profile_data={"files": ["a.py"]})

        assert result["tool_results"]["tech_detector"]["success"] is False
        assert "partial_failure" not in result
