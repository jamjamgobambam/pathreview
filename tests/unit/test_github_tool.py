"""Tests for github_tool.py"""

from datetime import date
from unittest.mock import Mock, patch

import httpx
import pytest

from agent.tools.github_tool import GitHubTool


def _repo_response() -> Mock:
    """Build a mock httpx.get response for the repo-metadata endpoint."""
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {
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
    return response


def _commits_page(commit_dates: list[str], next_url: str | None = None) -> Mock:
    """Build a mock httpx.get response for a page of the commits endpoint.

    Args:
        commit_dates: ISO 8601 date strings for `commit.author.date`
        next_url: If set, response.links will report a `rel="next"` page
    """
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = [{"commit": {"author": {"date": d}}} for d in commit_dates]
    response.links = {"next": {"url": next_url}} if next_url else {}
    return response


@pytest.mark.unit
class TestGitHubToolContributionStreak:
    """Tests for issue #52: contribution_streak field.

    GitHubTool._fetch_repo_metadata() fetches commit history via
    _fetch_commit_dates() and derives the longest run of consecutive
    calendar days via _compute_contribution_streak(). The first test below
    is the original reproduction test from Week 8 and now acts as a
    regression guard confirming the field stays present.
    """

    @pytest.fixture
    def tool(self) -> GitHubTool:
        """Create a GitHubTool instance."""
        return GitHubTool()

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_contribution_streak_field_present(
        self, mock_get: Mock, mock_head: Mock, tool: GitHubTool
    ) -> None:
        """contribution_streak is present in GitHubTool output (issue #52)."""
        mock_get.side_effect = [_repo_response(), _commits_page(["2026-07-28T21:54:36Z"])]

        mock_head_response = Mock()
        mock_head_response.status_code = 200
        mock_head.return_value = mock_head_response

        result = tool.execute({"github_username": "sameeraagkan", "repo_name": "Aura_"})

        assert result.success is True
        assert "contribution_streak" in result.data
        assert result.data["contribution_streak"] == 1

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_no_commits_gives_zero_streak(
        self, mock_get: Mock, mock_head: Mock, tool: GitHubTool
    ) -> None:
        """No commits by the author -> streak is 0, not an error."""
        mock_get.side_effect = [_repo_response(), _commits_page([])]
        mock_head.return_value = Mock(status_code=200)

        result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.success is True
        assert result.data["contribution_streak"] == 0

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_single_commit_gives_streak_of_one(
        self, mock_get: Mock, mock_head: Mock, tool: GitHubTool
    ) -> None:
        """Exactly one commit -> streak of 1."""
        mock_get.side_effect = [_repo_response(), _commits_page(["2026-01-05T10:00:00Z"])]
        mock_head.return_value = Mock(status_code=200)

        result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.data["contribution_streak"] == 1

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_non_consecutive_commits_use_longest_run(
        self, mock_get: Mock, mock_head: Mock, tool: GitHubTool
    ) -> None:
        """Commits with a gap only count the longest consecutive run."""
        dates = [
            "2026-01-01T09:00:00Z",
            "2026-01-02T09:00:00Z",
            "2026-01-03T09:00:00Z",
            # gap: 2026-01-04 has no commit
            "2026-01-05T09:00:00Z",
        ]
        mock_get.side_effect = [_repo_response(), _commits_page(dates)]
        mock_head.return_value = Mock(status_code=200)

        result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.data["contribution_streak"] == 3

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_same_day_commits_dedupe_to_one_day(
        self, mock_get: Mock, mock_head: Mock, tool: GitHubTool
    ) -> None:
        """Multiple commits on the same calendar day only count once."""
        dates = ["2026-01-01T09:00:00Z", "2026-01-01T15:00:00Z", "2026-01-01T23:00:00Z"]
        mock_get.side_effect = [_repo_response(), _commits_page(dates)]
        mock_head.return_value = Mock(status_code=200)

        result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.data["contribution_streak"] == 1

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_streak_spans_pagination_boundary(
        self, mock_get: Mock, mock_head: Mock, tool: GitHubTool
    ) -> None:
        """A consecutive run that crosses a page boundary is still counted whole."""
        page_1 = _commits_page(
            ["2026-01-01T09:00:00Z", "2026-01-02T09:00:00Z"],
            next_url="https://api.github.com/repos/octocat/Hello-World/commits?page=2",
        )
        page_2 = _commits_page(["2026-01-03T09:00:00Z", "2026-01-04T09:00:00Z"])
        mock_get.side_effect = [_repo_response(), page_1, page_2]
        mock_head.return_value = Mock(status_code=200)

        result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.data["contribution_streak"] == 4

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_commits_call_failure_degrades_to_zero_streak(
        self, mock_get: Mock, mock_head: Mock, tool: GitHubTool
    ) -> None:
        """Commits endpoint failing (e.g. rate limit) shouldn't fail the whole tool."""
        rate_limit_error = httpx.HTTPStatusError(
            "rate limited", request=Mock(), response=Mock(status_code=403)
        )
        mock_get.side_effect = [_repo_response(), rate_limit_error]
        mock_head.return_value = Mock(status_code=200)

        result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.success is True
        assert result.data["contribution_streak"] == 0
        # Other metadata that succeeded earlier should still be present.
        assert result.data["name"] == "Aura_"


@pytest.mark.unit
class TestComputeContributionStreak:
    """Direct tests of the pure streak-computation helper."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        return GitHubTool()

    def test_empty_list_gives_zero(self, tool: GitHubTool) -> None:
        assert tool._compute_contribution_streak([]) == 0

    def test_known_consecutive_run(self, tool: GitHubTool) -> None:
        dates = [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]
        assert tool._compute_contribution_streak(dates) == 3

    def test_unsorted_input_is_handled(self, tool: GitHubTool) -> None:
        dates = [date(2026, 1, 3), date(2026, 1, 1), date(2026, 1, 2)]
        assert tool._compute_contribution_streak(dates) == 3

    def test_picks_longest_of_multiple_runs(self, tool: GitHubTool) -> None:
        dates = [
            date(2026, 1, 1),
            date(2026, 1, 2),
            date(2026, 1, 10),
            date(2026, 1, 11),
            date(2026, 1, 12),
            date(2026, 1, 13),
        ]
        assert tool._compute_contribution_streak(dates) == 4
