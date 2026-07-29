"""Tests for github_tool.py"""

from unittest.mock import Mock, patch

import pytest

from agent.tools.github_tool import GitHubTool


@pytest.mark.unit
class TestGitHubToolContributionStreak:
    """Reproduction test for issue #52.

    GitHubTool._fetch_repo_metadata() only calls GET /repos/{owner}/{repo}
    and HEAD .../readme — there is no code path that fetches commit history,
    so the tool has no way to compute a contribution streak. This test
    documents that gap and is expected to fail until the fix (adding a
    contribution_streak field) lands.
    """

    @pytest.fixture
    def tool(self) -> GitHubTool:
        """Create a GitHubTool instance."""
        return GitHubTool()

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_contribution_streak_field_missing(
        self, mock_get: Mock, mock_head: Mock, tool: GitHubTool
    ) -> None:
        """Reproduces issue #52: contribution_streak is absent from tool output."""
        mock_repo_response = Mock()
        mock_repo_response.raise_for_status = Mock()
        mock_repo_response.json.return_value = {
            "name": "Aura_",
            "description": "test repo",
            "language": "TypeScript",
            "stargazers_count": 0,
            "forks_count": 0,
            "open_issues_count": 0,
            "pushed_at": "2026-07-28T21:54:36Z",
            "topics": [],
            "homepage": None,
        }
        mock_get.return_value = mock_repo_response

        mock_head_response = Mock()
        mock_head_response.status_code = 200
        mock_head.return_value = mock_head_response

        result = tool.execute({"github_username": "sameeraagkan", "repo_name": "Aura_"})

        assert result.success is True
        assert "contribution_streak" in result.data, (
            "contribution_streak field is missing from GitHubTool output — "
            "see issue #52. No code path in github_tool.py fetches commit "
            "history to compute it."
        )
