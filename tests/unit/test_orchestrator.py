"""Tests for Orchestrator plan validation and prerequisite gating (issue #54)."""

import pytest

from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult
from agent.tools.market_analyzer import MarketAnalyzer
from agent.tools.skill_extractor import SkillExtractor
from agent.tools.tech_detector import TechDetector
from agent.tools.tool_dependencies import PlanValidationError


class _StubTool(BaseTool):
    """Minimal tool that returns a preset ToolResult and records its inputs."""

    description = "stub tool"

    def __init__(self, name, result):
        self.name = name
        self._result = result
        self.calls = []

    def execute(self, input_data):
        self.calls.append(input_data)
        return self._result


@pytest.mark.unit
class TestOrchestratorPrerequisites:
    """End-to-end behavior of the dependency-aware orchestrator."""

    def test_market_analyzer_receives_skills_and_scores_nonzero(self):
        """Happy path: skill_extractor's output flows into market_analyzer."""
        tools = {
            "tech_detector": TechDetector(),
            "skill_extractor": SkillExtractor(),
            "market_analyzer": MarketAnalyzer(),
        }
        orch = Orchestrator(tools)
        profile = {
            "resume_text": "Python and TypeScript engineer using React, Docker, AWS, and SQL.",
            "files": ["main.py", "app.tsx", "Dockerfile"],
        }

        result = orch.run("profile-happy", profile)

        market = result["tool_results"]["market_analyzer"]
        assert market["market_alignment_score"] > 0.0
        assert market["in_demand_skills"]  # non-empty

    def test_dependent_skipped_when_prerequisite_fails(self):
        """A dependent whose prerequisite fails is skipped, never executed."""
        market = _StubTool("market_analyzer", ToolResult(success=True, data={"ran": True}))
        tools = {
            "tech_detector": _StubTool("tech_detector", ToolResult(success=True, data={})),
            "skill_extractor": _StubTool(
                "skill_extractor", ToolResult(success=False, data={}, error="boom")
            ),
            "market_analyzer": market,
        }
        orch = Orchestrator(tools)
        profile = {"resume_text": "x", "files": ["main.py"]}

        result = orch.run("profile-fail", profile)

        entry = result["tool_results"]["market_analyzer"]
        assert entry.get("skipped") is True
        assert "skill_extractor" in entry["reason"]
        assert market.calls == []  # market_analyzer never ran

    def test_invalid_plan_raises_before_execution(self, monkeypatch):
        """A mis-ordered plan raises PlanValidationError before any tool runs."""
        market = _StubTool("market_analyzer", ToolResult(success=True, data={}))
        tools = {
            "tech_detector": _StubTool("tech_detector", ToolResult(success=True, data={})),
            "skill_extractor": _StubTool("skill_extractor", ToolResult(success=True, data={})),
            "market_analyzer": market,
        }
        orch = Orchestrator(tools)
        bad_plan = [
            ("market_analyzer", {"detected_skills": {}}),
            ("skill_extractor", {"resume_text": "x"}),
            ("tech_detector", {"files": []}),
        ]
        monkeypatch.setattr(orch, "_build_plan", lambda profile_data: bad_plan)

        with pytest.raises(PlanValidationError):
            orch.run("profile-invalid", {"resume_text": "x"})

        assert market.calls == []  # execution never started
