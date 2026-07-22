"""Tests for github_tool.py

Includes a reproduction test for issue #52:
https://github.com/ascherj/pathreview/issues/52

    "Add a contribution_streak field to the GitHub analysis
     (longest consecutive days of commits)"

"""

from unittest.mock import MagicMock, patch

import pytest

from agent.tools.github_tool import GitHubTool


@pytest.mark.unit
class TestGitHubTool:
    """Test suite for GitHubTool."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        """Create a GitHubTool instance (unauthenticated)."""
        return GitHubTool()

    def _mock_repo_response(self) -> MagicMock:
        """Build a fake /repos/{owner}/{repo} JSON payload."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "name": "Hello-World",
            "description": "My first repository",
            "language": "Python",
            "stargazers_count": 42,
            "forks_count": 7,
            "open_issues_count": 3,
            "pushed_at": "2024-01-15T12:00:00Z",
            "topics": ["demo"],
            "homepage": "",
        }
        return mock_response

    def test_fetch_repo_metadata_returns_expected_snapshot_fields(self, tool: GitHubTool) -> None:
        """Sanity check: the tool returns the existing static-snapshot fields."""
        with (
            patch("agent.tools.github_tool.httpx.get") as mock_get,
            patch("agent.tools.github_tool.httpx.head") as mock_head,
        ):
            mock_get.return_value = self._mock_repo_response()
            mock_head.return_value = MagicMock(status_code=200)

            result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.success is True
        assert result.data["name"] == "Hello-World"
        assert result.data["primary_language"] == "Python"
        assert result.data["star_count"] == 42
        assert result.data["last_commit_date"] == "2024-01-15T12:00:00Z"

    @pytest.mark.xfail(
        strict=True,
        reason="Issue #52: contribution_streak is not implemented yet. "
        "GitHubTool never queries /repos/{owner}/{repo}/commits, so the "
        "returned metadata has no consecutive-commit-days signal.",
    )
    def test_repro_issue_52_metadata_includes_contribution_streak(self, tool: GitHubTool) -> None:
        """REPRODUCTION (#52): metadata should include `contribution_streak`.

        Two commits on 2024-01-14 and 2024-01-15 form a 2-day streak. The tool
        should fetch commit history, bucket commits by calendar day, and report
        the longest consecutive-day run. Today it does neither, so this fails.
        """
        commits_payload = [
            {"commit": {"author": {"date": "2024-01-15T09:00:00Z"}}},
            {"commit": {"author": {"date": "2024-01-14T18:00:00Z"}}},
        ]

        def fake_get(url: str, *args: object, **kwargs: object) -> MagicMock:
            if url.endswith("/commits"):
                resp = MagicMock()
                resp.raise_for_status.return_value = None
                resp.json.return_value = commits_payload
                resp.links = {}  # no further pages
                return resp
            return self._mock_repo_response()

        with (
            patch("agent.tools.github_tool.httpx.get", side_effect=fake_get),
            patch("agent.tools.github_tool.httpx.head") as mock_head,
        ):
            mock_head.return_value = MagicMock(status_code=200)

            result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.success is True
        assert (
            "contribution_streak" in result.data
        ), "GitHubTool metadata is missing the `contribution_streak` field"
        assert result.data["contribution_streak"] == 2
