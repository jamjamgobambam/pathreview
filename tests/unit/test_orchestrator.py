import pytest
from unittest.mock import Mock
from agent.orchestrator import Orchestrator

class TestOrchestratorFailureHandling:
    def test_run_signals_partial_failure_when_tool_crashes(self) -> None:
        """Verifies issue #44 fix: top-level partial_failure flag is True on tool crash."""
        failing_tool = Mock()
        failing_tool.execute.side_effect = Exception("tool crashed")
        
        successful_tool = Mock()
        successful_tool.execute.return_value = {"status": "ok"}
        
        orchestrator = Orchestrator(tools={
            "tech_detector": failing_tool,
            "market_analyzer": successful_tool
        })
        result = orchestrator.run(profile_id="test-1", profile_data={"files": ["a.py"]})
        
        assert result["tool_results"]["tech_detector"]["success"] is False
        assert "partial_failure" in result
        assert result["partial_failure"] is True

    def test_run_signals_no_partial_failure_when_tools_succeed(self) -> None:
        """Verifies partial_failure is False when all tools execute successfully."""
        successful_tool1 = Mock()
        successful_tool1.execute.return_value = {"status": "ok"}

        successful_tool2 = Mock()
        successful_tool2.execute.return_value = {"status": "ok"}
        
        orchestrator = Orchestrator(tools={
            "tech_detector": successful_tool1,
            "market_analyzer": successful_tool2
        })
        result = orchestrator.run(profile_id="test-2", profile_data={"files": ["a.py"]})
        
        assert "partial_failure" in result
        assert result["partial_failure"] is False