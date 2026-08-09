"""Tests for github_tool.py

Covers the `contribution_streak` field added for issue #52.
https://github.com/ascherj/pathreview/issues/52

`test_execute_returns_contribution_streak` began as the Week 8 reproduction
case (commit 5fa3296), where it failed because the field did not exist. It
passes now that the fix has landed.
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import httpx
import pytest

from agent.tools.github_tool import GitHubTool

# Minimal shape of GET /repos/{owner}/{repo}, trimmed to the keys the tool reads.
FAKE_REPO_JSON = {
    "name": "pathreview",
    "description": "AI-powered portfolio review",
    "language": "Python",
    "stargazers_count": 42,
    "forks_count": 7,
    "open_issues_count": 3,
    "pushed_at": "2026-07-20T12:00:00Z",
    "topics": ["ai", "fastapi"],
    "homepage": "https://example.com",
}

# Recent enough that the backward year-window loop terminates after one pass,
# which keeps the mocked GraphQL call count predictable.
RECENT_CREATED_AT = (datetime.now(UTC) - timedelta(days=30)).isoformat()


def graphql_calendar(day_counts: dict[str, int], created_at: str = RECENT_CREATED_AT) -> dict:
    """Build a GraphQL response body from a date -> contribution count mapping."""
    return {
        "data": {
            "user": {
                "createdAt": created_at,
                "contributionsCollection": {
                    "contributionCalendar": {
                        "weeks": [
                            {
                                "contributionDays": [
                                    {"date": day, "contributionCount": count}
                                    for day, count in sorted(day_counts.items())
                                ]
                            }
                        ]
                    }
                },
            }
        }
    }


class FakeResponse:
    """Stand-in for httpx.Response covering only what GitHubTool touches."""

    def __init__(self, json_data: dict, status_code: int = 200) -> None:
        self._json = json_data
        self.status_code = status_code

    def json(self) -> dict:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=MagicMock(), response=MagicMock()
            )


@pytest.mark.unit
class TestGitHubToolMetadata:
    """Repo metadata, including the contribution_streak field from issue #52."""

    @pytest.fixture
    def mocked_github(self) -> Iterator[tuple[MagicMock, MagicMock, MagicMock]]:
        """Patch the HTTP calls GitHubTool makes so tests never hit the network."""
        with (
            patch("agent.tools.github_tool.httpx.get") as mock_get,
            patch("agent.tools.github_tool.httpx.head") as mock_head,
            patch("agent.tools.github_tool.httpx.post") as mock_post,
        ):
            mock_get.return_value = FakeResponse(FAKE_REPO_JSON)
            mock_head.return_value = FakeResponse({}, status_code=200)
            mock_post.return_value = FakeResponse(
                graphql_calendar({"2026-07-01": 1, "2026-07-02": 3})
            )
            yield mock_get, mock_head, mock_post

    @staticmethod
    def _execute(tool: GitHubTool) -> dict:
        result = tool.execute(
            {"github_username": "ddzhang04", "repo_name": "pathreview"}
        )
        assert result.success is True
        return result.data

    def test_execute_succeeds_with_existing_metadata(
        self, mocked_github: tuple[MagicMock, MagicMock, MagicMock]
    ) -> None:
        """The pre-existing fields are unchanged by the #52 addition."""
        data = self._execute(GitHubTool())

        assert data["star_count"] == 42
        assert data["primary_language"] == "Python"
        assert data["has_readme"] is True

    def test_execute_returns_expected_field_set(
        self, mocked_github: tuple[MagicMock, MagicMock, MagicMock]
    ) -> None:
        """Pins the output shape: the ten original keys plus contribution_streak."""
        data = self._execute(GitHubTool())

        assert set(data.keys()) == {
            "name",
            "description",
            "primary_language",
            "star_count",
            "fork_count",
            "open_issues_count",
            "last_commit_date",
            "has_readme",
            "topics",
            "homepage",
            "contribution_streak",
        }

    def test_execute_returns_contribution_streak(
        self, mocked_github: tuple[MagicMock, MagicMock, MagicMock]
    ) -> None:
        """Issue #52: the streak is computed and returned alongside repo metadata.

        This is the Week 8 reproduction case, now passing.
        """
        data = self._execute(GitHubTool(api_token="fake-token"))

        assert data["contribution_streak"] == 2

    def test_streak_is_none_without_token_and_other_fields_survive(
        self, mocked_github: tuple[MagicMock, MagicMock, MagicMock]
    ) -> None:
        """GraphQL 403s unauthenticated, so the streak degrades without breaking the tool."""
        _, _, mock_post = mocked_github
        data = self._execute(GitHubTool())

        assert data["contribution_streak"] is None
        assert data["star_count"] == 42, "existing fields must keep working token-free"
        mock_post.assert_not_called()

    def test_streak_is_none_for_unknown_user(
        self, mocked_github: tuple[MagicMock, MagicMock, MagicMock]
    ) -> None:
        """A missing user returns data.user = null with HTTP 200, not an error status."""
        _, _, mock_post = mocked_github
        mock_post.return_value = FakeResponse({"data": {"user": None}})

        assert self._execute(GitHubTool(api_token="fake-token"))["contribution_streak"] is None

    def test_streak_is_none_on_graphql_errors(
        self, mocked_github: tuple[MagicMock, MagicMock, MagicMock]
    ) -> None:
        """GraphQL reports rate limits and bad scopes in an errors array, still HTTP 200."""
        _, _, mock_post = mocked_github
        mock_post.return_value = FakeResponse(
            {"errors": [{"message": "API rate limit exceeded"}]}
        )

        assert self._execute(GitHubTool(api_token="fake-token"))["contribution_streak"] is None

    def test_streak_is_none_on_http_failure(
        self, mocked_github: tuple[MagicMock, MagicMock, MagicMock]
    ) -> None:
        """A 403 mid-loop yields None rather than a partial, understated streak."""
        _, _, mock_post = mocked_github
        mock_post.return_value = FakeResponse({}, status_code=403)

        assert self._execute(GitHubTool(api_token="fake-token"))["contribution_streak"] is None

    def test_streak_failure_does_not_fail_the_whole_tool(
        self, mocked_github: tuple[MagicMock, MagicMock, MagicMock]
    ) -> None:
        """An unexpected GraphQL shape must not take down the repo metadata fetch."""
        _, _, mock_post = mocked_github
        mock_post.return_value = FakeResponse({"data": {"user": {"createdAt": "nonsense"}}})

        data = self._execute(GitHubTool(api_token="fake-token"))

        assert data["contribution_streak"] is None
        assert data["star_count"] == 42


@pytest.mark.unit
class TestLongestStreak:
    """The pure streak-scanning helper, exercised without any network."""

    @pytest.mark.parametrize(
        "days,expected",
        [
            pytest.param({}, 0, id="no-data"),
            pytest.param({"2026-07-01": 0, "2026-07-02": 0}, 0, id="all-zero-days"),
            pytest.param({"2026-07-01": 1}, 1, id="single-day"),
            pytest.param(
                {"2026-07-01": 1, "2026-07-02": 1, "2026-07-03": 1}, 3, id="unbroken-run"
            ),
            pytest.param(
                {"2026-07-01": 1, "2026-07-02": 0, "2026-07-03": 1}, 1, id="zero-day-breaks-run"
            ),
            pytest.param(
                {"2026-07-01": 1, "2026-07-05": 1, "2026-07-06": 1}, 2, id="missing-dates-break-run"
            ),
            pytest.param(
                {"2026-06-30": 1, "2026-07-01": 1, "2026-07-02": 1, "2026-07-09": 1},
                3,
                id="longest-run-wins-over-later-run",
            ),
        ],
    )
    def test_longest_streak(self, days: dict[str, int], expected: int) -> None:
        assert GitHubTool._longest_streak(days) == expected

    def test_streak_spans_a_year_boundary(self) -> None:
        """Dec 29 to Jan 2 is one 5-day run, not two runs split at the year edge.

        This is the case the year-by-year windowing would break if each window
        were scanned independently instead of merged first.
        """
        days = {
            "2025-12-29": 2,
            "2025-12-30": 1,
            "2025-12-31": 4,
            "2026-01-01": 1,
            "2026-01-02": 1,
        }

        assert GitHubTool._longest_streak(days) == 5

    def test_streak_spans_a_leap_day(self) -> None:
        """Feb 28 to Mar 1 2024 is unbroken only if Feb 29 is counted."""
        days = {"2024-02-28": 1, "2024-02-29": 1, "2024-03-01": 1}

        assert GitHubTool._longest_streak(days) == 3

    def test_trailing_zero_days_do_not_truncate_the_record(self) -> None:
        """A user mid-streak who has not contributed yet today keeps their best run."""
        days = {"2026-07-01": 1, "2026-07-02": 1, "2026-07-03": 1, "2026-07-04": 0}

        assert GitHubTool._longest_streak(days) == 3
