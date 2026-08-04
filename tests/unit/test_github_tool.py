"""Tests for github_tool.py — issue #52 contribution_streak."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from agent.tools.github_tool import GitHubTool


@pytest.mark.unit
class TestGitHubToolContributionStreak:
    """Tests for contribution_streak field (issue #52)."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        return GitHubTool()

    def _mock_repo_response(self) -> MagicMock:
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {
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
        mock.raise_for_status = MagicMock()
        return mock

    def _mock_commits_response(self, commit_dates: list[str]) -> MagicMock:
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = [{"commit": {"author": {"date": d}}} for d in commit_dates]
        mock.raise_for_status = MagicMock()
        return mock

    def test_metadata_includes_contribution_streak(self, tool: GitHubTool) -> None:
        """Tool output includes contribution_streak alongside other metadata."""
        mock_readme = MagicMock()
        mock_readme.status_code = 200

        def mock_get(
            url: str,
            headers: dict | None = None,
            params: dict | None = None,
            timeout: float | None = None,
        ) -> MagicMock:
            if url.endswith("/commits"):
                return self._mock_commits_response(["2024-01-01T10:00:00Z", "2024-01-02T10:00:00Z"])
            return self._mock_repo_response()

        with (
            patch("agent.tools.github_tool.httpx.get", side_effect=mock_get),
            patch("agent.tools.github_tool.httpx.head", return_value=mock_readme),
        ):
            result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.success is True
        assert "contribution_streak" in result.data
        assert result.data["contribution_streak"] == 2

    def test_calculate_longest_streak_consecutive_days(self, tool: GitHubTool) -> None:
        """Three consecutive days returns streak of 3."""
        dates = [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
        assert tool._calculate_longest_streak(dates) == 3

    def test_calculate_longest_streak_non_consecutive(self, tool: GitHubTool) -> None:
        """Gap in dates — longest streak is 2 not 3."""
        dates = [date(2024, 1, 1), date(2024, 1, 3), date(2024, 1, 4)]
        assert tool._calculate_longest_streak(dates) == 2

    def test_calculate_longest_streak_single_day(self, tool: GitHubTool) -> None:
        """One day with commits returns streak of 1."""
        assert tool._calculate_longest_streak([date(2024, 1, 1)]) == 1

    def test_calculate_longest_streak_empty(self, tool: GitHubTool) -> None:
        """No commit dates returns streak of 0."""
        assert tool._calculate_longest_streak([]) == 0

    def test_calculate_longest_streak_deduplicates_same_day(self, tool: GitHubTool) -> None:
        """Multiple commits on same day count as one day."""
        dates = [date(2024, 1, 1), date(2024, 1, 1), date(2024, 1, 2)]
        assert tool._calculate_longest_streak(dates) == 2

    def test_contribution_streak_no_commits(self, tool: GitHubTool) -> None:
        """Empty commit history returns contribution_streak of 0."""
        mock_readme = MagicMock()
        mock_readme.status_code = 200

        def mock_get(
            url: str,
            headers: dict | None = None,
            params: dict | None = None,
            timeout: float | None = None,
        ) -> MagicMock:
            if url.endswith("/commits"):
                mock = MagicMock()
                mock.status_code = 200
                mock.json.return_value = []
                mock.raise_for_status = MagicMock()
                return mock
            return self._mock_repo_response()

        with (
            patch("agent.tools.github_tool.httpx.get", side_effect=mock_get),
            patch("agent.tools.github_tool.httpx.head", return_value=mock_readme),
        ):
            result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.success is True
        assert result.data["contribution_streak"] == 0

    def test_contribution_streak_api_error_fallback(self, tool: GitHubTool) -> None:
        """If commits API fails, tool still succeeds with streak 0."""
        mock_readme = MagicMock()
        mock_readme.status_code = 200

        def mock_get(
            url: str,
            headers: dict | None = None,
            params: dict | None = None,
            timeout: float | None = None,
        ) -> MagicMock:
            if url.endswith("/commits"):
                mock = MagicMock()
                mock.raise_for_status.side_effect = Exception("API error")
                return mock
            return self._mock_repo_response()

        with (
            patch("agent.tools.github_tool.httpx.get", side_effect=mock_get),
            patch("agent.tools.github_tool.httpx.head", return_value=mock_readme),
        ):
            result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.success is True
        assert result.data["contribution_streak"] == 0
        assert "star_count" in result.data
