"""Tests for github_tool.py to reproduce issue #52."""

from unittest.mock import MagicMock, patch

import pytest

from agent.tools.github_tool import GitHubTool


@pytest.mark.unit
class TestGitHubToolContributionStreak:
    """Reproduce missing contribution_streak field (issue #52)."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        return GitHubTool()

    def test_metadata_missing_contribution_streak(self, tool: GitHubTool) -> None:
        """Reproduction: github_tool returns repo metadata but no contribution_streak."""
        mock_repo_response = MagicMock()
        mock_repo_response.status_code = 200
        mock_repo_response.json.return_value = {
            "name": "Hello-World",
            "description": "My first repo",
            "language": "Python",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 2,
            "pushed_at": "2024-01-15T12:00:00Z",
            "topics": [],
            "homepage": "",
        }
        mock_repo_response.raise_for_status = MagicMock()

        mock_readme_response = MagicMock()
        mock_readme_response.status_code = 200

        with (
            patch("agent.tools.github_tool.httpx.get", return_value=mock_repo_response),
            patch("agent.tools.github_tool.httpx.head", return_value=mock_readme_response),
        ):
            result = tool.execute(
                {
                    "github_username": "octocat",
                    "repo_name": "Hello-World",
                }
            )

        assert result.success is True
        assert "star_count" in result.data
        assert "last_commit_date" in result.data
        # Issue #52: this field should exist but does not yet
        assert "contribution_streak" in result.data
