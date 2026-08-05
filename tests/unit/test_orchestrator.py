"""Tests for orchestrator.py"""

from unittest.mock import Mock

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult
from agent.tools.market_analyzer import MarketAnalyzer
from agent.tools.skill_extractor import SkillExtractor


class CountingTool(BaseTool):
    """Fake tool that records how many times it was actually executed."""

    name = "tech_detector"
    description = "Fake tool for counting real executions"

    def __init__(self):
        self.call_count = 0

    def execute(self, input_data: dict) -> ToolResult:
        self.call_count += 1
        return ToolResult(success=True, data={"call_count": self.call_count})


@pytest.mark.unit
class TestOrchestrator:
    """Test suite for Orchestrator session/cache isolation between reviews."""

    def test_tool_results_not_memoized_across_runs(self):
        """A second run() with identical input must re-execute tools, not
        reuse the previous review's memoized result."""
        counting_tool = CountingTool()
        orchestrator = Orchestrator(tools={"tech_detector": counting_tool})
        profile_data = {"files": ["main.py", "utils.py"]}

        first = orchestrator.run("profile-1", profile_data)
        second = orchestrator.run("profile-1", profile_data)

        assert counting_tool.call_count == 2
        assert first["tool_results"]["tech_detector"]["call_count"] == 1
        assert second["tool_results"]["tech_detector"]["call_count"] == 2

    def test_market_analyzer_reflects_current_run_skills(self):
        """market_analyzer should score whatever skills were detected in
        the current run, not a hardcoded empty dict."""
        orchestrator = Orchestrator(
            tools={
                "skill_extractor": SkillExtractor(),
                "market_analyzer": MarketAnalyzer(),
            }
        )
        profile_data = {"resume_text": "Experienced Python developer with Docker skills."}

        result = orchestrator.run("profile-1", profile_data)

        in_demand = {
            s["skill"] for s in result["tool_results"]["market_analyzer"]["in_demand_skills"]
        }
        assert "Python" in in_demand
        assert "Docker" in in_demand

    def test_market_analyzer_output_changes_between_reviews(self):
        """Reproduces the issue scenario: a second review after the user's
        portfolio changes must not reuse the first review's stale results."""
        orchestrator = Orchestrator(
            tools={
                "skill_extractor": SkillExtractor(),
                "market_analyzer": MarketAnalyzer(),
            }
        )

        first = orchestrator.run("profile-1", {"resume_text": "Skilled in Python and Docker."})
        second = orchestrator.run("profile-1", {"resume_text": "Skilled in Rust only."})

        first_skills = {
            s["skill"] for s in first["tool_results"]["market_analyzer"]["in_demand_skills"]
        }
        second_skills = {
            s["skill"] for s in second["tool_results"]["market_analyzer"]["in_demand_skills"]
        }

        assert "Python" in first_skills
        assert "Python" not in second_skills
        assert "Rust" in second_skills

    def test_session_state_replaced_not_merged(self):
        """Redis-backed session state should be replaced with the current
        review's results, not merged with (and never read from) a prior
        review's stale state."""
        mock_session_store = Mock(spec=SessionStore)
        counting_tool = CountingTool()
        orchestrator = Orchestrator(
            tools={"tech_detector": counting_tool},
            session_store=mock_session_store,
        )
        profile_data = {"files": ["main.py"]}

        result = orchestrator.run("profile-1", profile_data)

        mock_session_store.get.assert_not_called()
        mock_session_store.set.assert_called_once_with("profile-1", result["tool_results"])
