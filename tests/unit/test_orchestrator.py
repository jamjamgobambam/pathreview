"""Tests for orchestrator.py plan building.

These cover the pure planning logic in Orchestrator._build_plan, which decides
which tools run for a given profile. It needs no database, Redis, or network, so
it is a good fit for fast unit coverage of the conditional and boundary behavior.
"""

import pytest

from agent.orchestrator import Orchestrator


@pytest.mark.unit
class TestOrchestratorPlan:
    """Test suite for Orchestrator._build_plan."""

    @pytest.fixture
    def orchestrator(self):
        """Create an Orchestrator with no tools or session store."""
        return Orchestrator(tools={})

    def test_empty_profile_returns_empty_plan(self, orchestrator):
        """A profile with no usable fields should produce no plan steps."""
        plan = orchestrator._build_plan({})

        assert plan == []

    def test_readme_content_schedules_readme_scorer(self, orchestrator):
        """readme_content should schedule the readme_scorer tool."""
        plan = orchestrator._build_plan({"readme_content": "# My project"})
        tool_names = [name for name, _ in plan]

        assert "readme_scorer" in tool_names

    def test_files_schedule_tech_detector(self, orchestrator):
        """A files list should schedule the tech_detector tool."""
        plan = orchestrator._build_plan({"files": ["main.py", "app.js"]})
        tool_names = [name for name, _ in plan]

        assert "tech_detector" in tool_names

    def test_resume_text_schedules_skill_extractor(self, orchestrator):
        """resume_text should schedule the skill_extractor tool."""
        plan = orchestrator._build_plan({"resume_text": "Python and Django experience"})
        tool_names = [name for name, _ in plan]

        assert "skill_extractor" in tool_names

    def test_github_username_without_repos_skips_github_tool(self, orchestrator):
        """A username with no project repos should not schedule github_tool."""
        plan = orchestrator._build_plan(
            {"github_username": "octocat", "projects": [{"name": "no repo here"}]}
        )
        tool_names = [name for name, _ in plan]

        assert "github_tool" not in tool_names

    def test_github_tool_uses_only_first_repo(self, orchestrator):
        """Only the first project with a github_repo should be planned."""
        plan = orchestrator._build_plan(
            {
                "github_username": "octocat",
                "projects": [
                    {"github_repo": "first"},
                    {"github_repo": "second"},
                ],
            }
        )
        github_steps = [step for step in plan if step[0] == "github_tool"]

        assert len(github_steps) == 1
        assert github_steps[0][1]["repo_name"] == "first"

    def test_market_analyzer_only_added_when_other_tools_run(self, orchestrator):
        """market_analyzer should append when the plan has work, and not otherwise."""
        empty_plan = orchestrator._build_plan({})
        populated_plan = orchestrator._build_plan({"readme_content": "# Hi"})

        empty_names = [name for name, _ in empty_plan]
        populated_names = [name for name, _ in populated_plan]

        assert "market_analyzer" not in empty_names
        assert "market_analyzer" in populated_names
