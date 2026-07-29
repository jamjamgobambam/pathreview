"""Unit tests for GitHub contribution streak analysis."""

from unittest.mock import Mock, patch

import httpx
import pytest

from agent.tools.github_tool import GitHubTool

pytestmark = pytest.mark.unit

REPO_RESPONSE = {
    "name": "sample-repo",
    "description": "Sample repository",
    "language": "Python",
    "stargazers_count": 7,
    "forks_count": 2,
    "open_issues_count": 1,
    "pushed_at": "2026-07-20T12:00:00Z",
    "topics": ["python", "testing"],
    "homepage": "https://example.com",
}


def _configure_repo_responses(mock_get: Mock, mock_head: Mock) -> None:
    """Configure successful repository metadata responses."""
    repo_response = Mock()
    repo_response.json.return_value = REPO_RESPONSE
    repo_response.raise_for_status.return_value = None
    mock_get.return_value = repo_response
    mock_head.return_value.status_code = 200


@pytest.mark.parametrize(
    ("dates", "expected"),
    [
        ([], 0),
        (["2026-07-01"], 1),
        (["2026-07-01", "2026-07-02", "2026-07-03"], 3),
        (["2026-07-01", "2026-07-01", "2026-07-02"], 2),
        (["2026-07-03", "2026-07-01", "2026-07-02"], 3),
        (["2026-07-01", "2026-07-03", "2026-07-04", "2026-07-05"], 3),
        (["2026-01-30", "2026-01-31", "2026-02-01"], 3),
        (["2025-12-31", "2026-01-01", "2026-01-02"], 3),
    ],
    ids=[
        "no-dates",
        "one-day",
        "consecutive-days",
        "duplicate-dates",
        "unsorted-dates",
        "separate-streaks",
        "month-boundary",
        "year-boundary",
    ],
)
def test_calculate_longest_streak(dates: list[str], expected: int) -> None:
    """Calculate the longest streak from unique sorted calendar dates."""
    assert GitHubTool._calculate_longest_streak(dates) == expected


@patch("agent.tools.github_tool.httpx.post")
@patch("agent.tools.github_tool.httpx.head")
@patch("agent.tools.github_tool.httpx.get")
def test_execute_adds_streak_without_changing_metadata(
    mock_get: Mock, mock_head: Mock, mock_post: Mock
) -> None:
    """Add contribution_streak while preserving repository metadata."""
    _configure_repo_responses(mock_get, mock_head)
    contribution_response = Mock()
    contribution_response.raise_for_status.return_value = None
    contribution_response.json.return_value = {
        "data": {
            "user": {
                "contributionsCollection": {
                    "commitContributionsByRepository": [
                        {
                            "contributions": {
                                "nodes": [
                                    {"occurredAt": "2026-07-01T12:00:00Z"},
                                    {"occurredAt": "2026-07-02T09:00:00Z"},
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }
    mock_post.return_value = contribution_response

    result = GitHubTool(api_token="test-token").execute(
        {"github_username": "octocat", "repo_name": "sample-repo"}
    )

    assert result.success is True
    assert result.data == {
        "name": "sample-repo",
        "description": "Sample repository",
        "primary_language": "Python",
        "star_count": 7,
        "fork_count": 2,
        "open_issues_count": 1,
        "last_commit_date": "2026-07-20T12:00:00Z",
        "has_readme": True,
        "topics": ["python", "testing"],
        "homepage": "https://example.com",
        "contribution_streak": 2,
    }
    mock_post.assert_called_once()


@patch("agent.tools.github_tool.httpx.head")
@patch("agent.tools.github_tool.httpx.get")
def test_execute_requires_token_for_contribution_history(mock_get: Mock, mock_head: Mock) -> None:
    """Fail when contribution history cannot be authenticated."""
    _configure_repo_responses(mock_get, mock_head)

    result = GitHubTool().execute({"github_username": "octocat", "repo_name": "sample-repo"})

    assert result.success is False
    assert result.data == {}
    assert result.error == "GitHub API token required for contribution history"


@patch("agent.tools.github_tool.httpx.post")
@patch("agent.tools.github_tool.httpx.head")
@patch("agent.tools.github_tool.httpx.get")
def test_execute_fails_when_contribution_request_fails(
    mock_get: Mock, mock_head: Mock, mock_post: Mock
) -> None:
    """Fail the tool instead of returning a zero streak after an HTTP error."""
    _configure_repo_responses(mock_get, mock_head)
    request = httpx.Request("POST", "https://api.github.com/graphql")
    response = httpx.Response(502, request=request)
    mock_post.side_effect = httpx.HTTPStatusError(
        "GitHub request failed", request=request, response=response
    )

    result = GitHubTool(api_token="test-token").execute(
        {"github_username": "octocat", "repo_name": "sample-repo"}
    )

    assert result.success is False
    assert result.data == {}
    assert result.error == "GitHub API error: 502"


@patch("agent.tools.github_tool.httpx.post")
@patch("agent.tools.github_tool.httpx.head")
@patch("agent.tools.github_tool.httpx.get")
def test_execute_fails_when_graphql_returns_errors(
    mock_get: Mock, mock_head: Mock, mock_post: Mock
) -> None:
    """Fail the tool when GitHub returns GraphQL errors with HTTP 200."""
    _configure_repo_responses(mock_get, mock_head)
    contribution_response = Mock()
    contribution_response.raise_for_status.return_value = None
    contribution_response.json.return_value = {"errors": [{"message": "Contribution query failed"}]}
    mock_post.return_value = contribution_response

    result = GitHubTool(api_token="test-token").execute(
        {"github_username": "octocat", "repo_name": "sample-repo"}
    )

    assert result.success is False
    assert result.data == {}
    assert result.error is not None
    assert "contribution" in result.error.lower()
