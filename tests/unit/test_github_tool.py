"""Tests for github_tool.py

Includes a reproduction test for issue #52:
https://github.com/ascherj/pathreview/issues/52

    "Add a contribution_streak field to the GitHub analysis
     (longest consecutive days of commits)"

"""

from datetime import date
from unittest.mock import MagicMock, patch

import httpx
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

    def test_repro_issue_52_metadata_includes_contribution_streak(self, tool: GitHubTool) -> None:
        """REGRESSION (#52): metadata should include `contribution_streak`.

        Two commits on 2024-01-14 and 2024-01-15 form a 2-day streak. The tool
        fetches commit history, buckets commits by calendar day, and reports the
        longest consecutive-day run.
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

    # --- _longest_streak (pure helper) ------------------------------------

    def test_longest_streak_empty_set_is_zero(self, tool: GitHubTool) -> None:
        """No commits (empty/brand-new repo) → streak of 0."""
        assert tool._longest_streak(set()) == 0

    def test_longest_streak_single_day_is_one(self, tool: GitHubTool) -> None:
        """All commits on one day (e.g. a hackathon) → streak of 1, not a count."""
        assert tool._longest_streak({date(2024, 1, 15)}) == 1

    def test_longest_streak_picks_longest_run_across_gaps(self, tool: GitHubTool) -> None:
        """Jan 13,14,15 then a gap then Jan 18,19 → longest run is 3."""
        days = {
            date(2024, 1, 13),
            date(2024, 1, 14),
            date(2024, 1, 15),
            date(2024, 1, 18),
            date(2024, 1, 19),
        }
        assert tool._longest_streak(days) == 3

    def test_longest_streak_ignores_input_order(self, tool: GitHubTool) -> None:
        """A set is unordered, so the calc must not assume chronological input."""
        days = {date(2024, 2, 3), date(2024, 2, 1), date(2024, 2, 2)}
        assert tool._longest_streak(days) == 3

    def test_longest_streak_crosses_month_boundary(self, tool: GitHubTool) -> None:
        """Consecutive days spanning a month boundary still count as one run."""
        days = {date(2024, 1, 30), date(2024, 1, 31), date(2024, 2, 1)}
        assert tool._longest_streak(days) == 3

    # --- _fetch_commit_dates (pagination + failure) -----------------------

    def test_fetch_commit_dates_follows_pagination(self, tool: GitHubTool) -> None:
        """Commits split across pages are all collected by following `next`."""
        page1 = MagicMock()
        page1.raise_for_status.return_value = None
        page1.json.return_value = [{"commit": {"author": {"date": "2024-01-15T09:00:00Z"}}}]
        page1.links = {"next": {"url": "https://api.github.com/next-page"}}

        page2 = MagicMock()
        page2.raise_for_status.return_value = None
        page2.json.return_value = [{"commit": {"author": {"date": "2024-01-14T18:00:00Z"}}}]
        page2.links = {}  # last page

        with patch("agent.tools.github_tool.httpx.get", side_effect=[page1, page2]) as mock_get:
            dates = tool._fetch_commit_dates("octocat", "Hello-World")

        assert dates == [date(2024, 1, 15), date(2024, 1, 14)]
        assert mock_get.call_count == 2
        # Second call targets the `next` link, not the base commits URL.
        assert mock_get.call_args_list[1].args[0] == "https://api.github.com/next-page"

    def test_fetch_commit_dates_degrades_to_empty_on_error(self, tool: GitHubTool) -> None:
        """A failing /commits request degrades to [] rather than raising."""
        with patch(
            "agent.tools.github_tool.httpx.get",
            side_effect=httpx.RequestError("boom"),
        ):
            assert tool._fetch_commit_dates("octocat", "Hello-World") == []

    def test_execute_degrades_streak_to_zero_when_commits_fail(self, tool: GitHubTool) -> None:
        """If /commits fails but the repo lookup succeeds, streak is 0 and the
        other metadata still comes back successfully (edge case #5)."""

        def fake_get(url: str, *args: object, **kwargs: object) -> MagicMock:
            if url.endswith("/commits"):
                raise httpx.RequestError("commits unavailable")
            return self._mock_repo_response()

        with (
            patch("agent.tools.github_tool.httpx.get", side_effect=fake_get),
            patch("agent.tools.github_tool.httpx.head") as mock_head,
        ):
            mock_head.return_value = MagicMock(status_code=200)
            result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

        assert result.success is True
        assert result.data["name"] == "Hello-World"
        assert result.data["contribution_streak"] == 0
