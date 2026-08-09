"""Tests for agent orchestrator planning."""

import pytest

from agent.orchestrator import Orchestrator


@pytest.mark.unit
class TestOrchestratorPlanning:
    """Tests for orchestrator plan construction."""

    def test_repository_project_schedules_dependency_audit(self) -> None:
        """A GitHub-backed project should schedule dependency auditing."""
        orchestrator = Orchestrator(tools={})

        plan = orchestrator._build_plan(
            {
                "github_username": "example-user",
                "projects": [
                    {
                        "github_repo": "example-project",
                    }
                ],
            }
        )

        assert (
            "dependency_audit",
            {
                "github_username": "example-user",
                "repo_name": "example-project",
            },
        ) in plan

    def test_repository_project_keeps_github_tool(self) -> None:
        """Adding dependency auditing should preserve GitHub metadata analysis."""
        orchestrator = Orchestrator(tools={})

        plan = orchestrator._build_plan(
            {
                "github_username": "example-user",
                "projects": [
                    {
                        "github_repo": "example-project",
                    }
                ],
            }
        )

        assert (
            "github_tool",
            {
                "github_username": "example-user",
                "repo_name": "example-project",
            },
        ) in plan

    def test_profile_without_repository_does_not_schedule_dependency_audit(self) -> None:
        """Profiles without a repository should not schedule the audit."""
        orchestrator = Orchestrator(tools={})

        plan = orchestrator._build_plan(
            {
                "github_username": "example-user",
                "projects": [],
            }
        )

        tool_names = [tool_name for tool_name, _ in plan]

        assert "dependency_audit" not in tool_names
