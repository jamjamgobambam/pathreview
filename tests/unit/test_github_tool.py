"""Tests for github_tool.py"""

from unittest.mock import MagicMock, patch

import pytest

from agent.tools.github_tool import GitHubTool


def _calendar_response(dates_with_counts: list[tuple[str, int]]) -> MagicMock:
    """Build a fake httpx.Response for the contributionsCollection query."""
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "data": {
            "user": {
                "contributionsCollection": {
                    "contributionCalendar": {
                        "weeks": [
                            {
                                "contributionDays": [
                                    {"date": date_str, "contributionCount": count}
                                    for date_str, count in dates_with_counts
                                ]
                            }
                        ]
                    }
                }
            }
        }
    }
    return response


@pytest.mark.unit
class TestLongestContributionStreak:
    """Test suite for GitHubTool._longest_contribution_streak."""

    @pytest.fixture
    def tool(self):
        """Create a GitHubTool instance with a fake token."""
        return GitHubTool(api_token="fake-token")

    def test_no_token_returns_zero_without_request(self):
        """Without a token, the GraphQL call can't authenticate, so bail out early."""
        tool = GitHubTool(api_token=None)
        with patch("httpx.post") as mock_post:
            assert tool._longest_contribution_streak("someone") == 0
            mock_post.assert_not_called()

    def test_no_contributions_returns_zero(self, tool):
        with patch(
            "httpx.post",
            return_value=_calendar_response(
                [
                    ("2026-01-01", 0),
                    ("2026-01-02", 0),
                ]
            ),
        ):
            assert tool._longest_contribution_streak("someone") == 0

    def test_single_contribution_day_returns_one(self, tool):
        with patch(
            "httpx.post",
            return_value=_calendar_response(
                [
                    ("2026-01-01", 0),
                    ("2026-01-02", 3),
                    ("2026-01-03", 0),
                ]
            ),
        ):
            assert tool._longest_contribution_streak("someone") == 1

    def test_unbroken_streak(self, tool):
        dates = [(f"2026-01-{day:02d}", 1) for day in range(1, 11)]
        with patch("httpx.post", return_value=_calendar_response(dates)):
            assert tool._longest_contribution_streak("someone") == 10

    def test_streak_with_gap_returns_longest_not_total(self, tool):
        # 10 consecutive days, a 2-day gap, then 3 more consecutive days.
        dense_run = [(f"2026-01-{day:02d}", 1) for day in range(1, 11)]
        gap = [("2026-01-11", 0), ("2026-01-12", 0)]
        short_run = [(f"2026-01-{day:02d}", 1) for day in range(13, 16)]
        with patch("httpx.post", return_value=_calendar_response(dense_run + gap + short_run)):
            assert tool._longest_contribution_streak("someone") == 10

    def test_same_day_multiple_contributions_counts_once(self, tool):
        with patch(
            "httpx.post",
            return_value=_calendar_response(
                [
                    ("2026-01-01", 5),
                ]
            ),
        ):
            assert tool._longest_contribution_streak("someone") == 1

    def test_nonexistent_user_returns_zero(self, tool):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "data": {"user": None},
            "errors": [{"message": "Could not resolve to a User"}],
        }
        with patch("httpx.post", return_value=response):
            assert tool._longest_contribution_streak("ghost") == 0

    def test_request_exception_returns_zero(self, tool):
        with patch("httpx.post", side_effect=Exception("network error")):
            assert tool._longest_contribution_streak("someone") == 0

    def test_wired_into_repo_metadata(self, tool):
        """_fetch_repo_metadata should include the streak alongside existing fields."""
        repo_response = MagicMock()
        repo_response.raise_for_status.return_value = None
        repo_response.json.return_value = {
            "name": "repo",
            "description": "desc",
            "language": "Python",
            "stargazers_count": 1,
            "forks_count": 0,
            "open_issues_count": 0,
            "pushed_at": "2026-01-01T00:00:00Z",
            "topics": [],
            "homepage": None,
        }
        readme_response = MagicMock(status_code=200)
        streak_response = _calendar_response([("2026-01-01", 1), ("2026-01-02", 1)])

        with (
            patch("httpx.get", side_effect=[repo_response, readme_response]),
            patch("httpx.post", return_value=streak_response),
        ):
            metadata = tool._fetch_repo_metadata("someone", "repo")

        assert metadata["contribution_streak"] == 2
