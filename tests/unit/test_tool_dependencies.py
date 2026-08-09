"""Tests to verify the plan validation/dependency engine (Issue #54).

These tests verify that the Orchestrator constructs and executes plans
by validating prerequisites, topological order, and circular dependencies.
"""

import pytest

from agent.orchestrator import Orchestrator
from agent.tools.market_analyzer import MarketAnalyzer
from agent.tools.readme_scorer import ReadmeScorer
from agent.tools.skill_extractor import SkillExtractor
from agent.tools.tech_detector import TechDetector
from agent.tools.tool_dependencies import PlanValidationError, PlanValidator


@pytest.mark.unit
class TestOrchestratorDependencyBug:
    """Test suite demonstrating tool prerequisite validation."""

    @pytest.fixture
    def tools(self):
        """Create dictionary of real tool instances."""
        return {
            "tech_detector": TechDetector(),
            "readme_scorer": ReadmeScorer(),
            "skill_extractor": SkillExtractor(),
            "market_analyzer": MarketAnalyzer(),
        }

    @pytest.fixture
    def orchestrator(self, tools):
        """Create an Orchestrator instance with the tools."""
        return Orchestrator(tools=tools)

    def test_orchestrator_runs_with_missing_dependencies(self, orchestrator):
        """Verifies that Orchestrator raises PlanValidationError when missing dependencies occur.

        In this test, we run 'market_analyzer' directly via a profile that has no preceding
        tools in the execution plan to supply skills (e.g. no resume_text provided).
        The orchestrator should raise a PlanValidationError.
        """
        profile_data = {
            "github_username": "testuser",
            "projects": [{"github_repo": "testrepo"}],
        }

        # Manually craft a plan with unsatisfied dependencies
        plan = [("market_analyzer", {"detected_skills": {}})]
        orchestrator._build_plan = lambda x: plan

        # Expect PlanValidationError due to missing prerequisites
        with pytest.raises(PlanValidationError) as excinfo:
            orchestrator.run("profile_1", profile_data)

        assert "prerequisite" in str(excinfo.value).lower()

    def test_orchestrator_automatically_corrects_out_of_order(self, orchestrator):
        """Verifies that Orchestrator automatically corrects and executes an out-of-order plan.

        If we provide a plan where all tools are present but completely out of topological order
        (e.g., market_analyzer -> skill_extractor -> tech_detector), the orchestrator should
        topologically sort the plan and execute it successfully without raising any error.
        """
        plan = [
            ("market_analyzer", {"detected_skills": {}}),
            ("skill_extractor", {"resume_text": "Python, SQL, React", "repo_metadata": {}}),
            ("tech_detector", {"files": ["main.py"]}),
        ]
        orchestrator._build_plan = lambda x: plan

        # Execute orchestrator. It should automatically correct the order and succeed!
        result = orchestrator.run("profile_2", {})

        # Confirm that orchestrator successfully ran all tools
        assert "market_analyzer" in result["tool_results"]
        assert "skill_extractor" in result["tool_results"]
        assert "tech_detector" in result["tool_results"]

    def test_orchestrator_circular_dependencies(self, orchestrator):
        """Verifies that Orchestrator raises PlanValidationError if there is a circular dependency.

        If a circular dependency exists in the dependency definitions, validation should fail.
        """
        # Create a custom PlanValidator with a circular dependency: A -> B -> A
        circular_deps = {
            "tool_a": ["tool_b"],
            "tool_b": ["tool_a"],
        }
        validator = PlanValidator(dependencies=circular_deps)

        with pytest.raises(PlanValidationError) as excinfo:
            validator.validate_plan([("tool_a", {})], {})

        assert "circular dependency" in str(excinfo.value).lower()
