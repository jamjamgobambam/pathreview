"""Tests for orchestrator.py"""

import pytest

from agent.orchestrator import Orchestrator


@pytest.mark.unit
class TestOrchestrator:
    """Test suite for Orchestrator planning."""

    def test_build_plan_includes_repo_analyzer_with_files(self) -> None:
        """Test repo_analyzer is scheduled when file data is available."""
        orchestrator = Orchestrator(tools={})

        plan = orchestrator._build_plan(
            {
                "github_username": "demo-user",
                "projects": [{"github_repo": "demo-repo"}],
                "files": ["tests/test_app.py", "src/app.py"],
            }
        )

        tool_names = [tool_name for tool_name, _ in plan]

        assert "github_tool" in tool_names
        assert "tech_detector" in tool_names
        assert "repo_analyzer" in tool_names
        assert "market_analyzer" in tool_names

    def test_build_plan_skips_repo_analyzer_without_files(self) -> None:
        """Test repo_analyzer is skipped if no file list exists."""
        orchestrator = Orchestrator(tools={})

        plan = orchestrator._build_plan(
            {
                "github_username": "demo-user",
                "projects": [{"github_repo": "demo-repo"}],
            }
        )

        tool_names = [tool_name for tool_name, _ in plan]

        assert "repo_analyzer" not in tool_names
