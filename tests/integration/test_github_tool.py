"""Integration tests for GitHubTool against a local mock GitHub API server.

These tests use pytest-httpserver to stand up a real HTTP server on localhost that serves
canned fixture responses from ``tests/fixtures/github_responses``. That lets the tool's
request handling and error paths run deterministically and offline in CI, without live
network access, GitHub authentication, or rate limits.
"""

import json
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from agent.tools.github_tool import GitHubTool

pytestmark = pytest.mark.integration

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "github_responses"

USERNAME = "janedoe"
REPO_NAME = "weather-app"


def load_fixture(name: str) -> dict:
    """Load a canned GitHub API response.

    Args:
        name: Fixture file stem, e.g. "repo_success"

    Returns:
        The parsed JSON body
    """
    payload: dict = json.loads((FIXTURE_DIR / f"{name}.json").read_text())
    return payload


def register_repo(
    httpserver: HTTPServer,
    payload: dict,
    status: int = 200,
    username: str = USERNAME,
    repo_name: str = REPO_NAME,
) -> None:
    """Register the GET /repos/{username}/{repo_name} route on the mock server."""
    httpserver.expect_request(f"/repos/{username}/{repo_name}", method="GET").respond_with_json(
        payload, status=status
    )


def register_readme(
    httpserver: HTTPServer,
    status: int = 200,
    username: str = USERNAME,
    repo_name: str = REPO_NAME,
) -> None:
    """Register the HEAD /repos/{username}/{repo_name}/readme route on the mock server."""
    httpserver.expect_request(
        f"/repos/{username}/{repo_name}/readme", method="HEAD"
    ).respond_with_data("", status=status)


@pytest.fixture
def github_tool(httpserver: HTTPServer) -> GitHubTool:
    """Return a GitHubTool pointed at the mock server instead of api.github.com."""
    return GitHubTool(base_url=httpserver.url_for(""))


def test_execute_maps_repo_metadata_on_success(
    httpserver: HTTPServer, github_tool: GitHubTool
) -> None:
    """A 200 response is mapped field-by-field onto the ToolResult data."""
    payload = load_fixture("repo_success")
    register_repo(httpserver, payload)
    register_readme(httpserver, status=200)

    result = github_tool.execute({"github_username": USERNAME, "repo_name": REPO_NAME})

    assert result.success is True
    assert result.error is None
    assert result.data == {
        "name": "weather-app",
        "description": payload["description"],
        "primary_language": "TypeScript",
        "star_count": 42,
        "fork_count": 7,
        "open_issues_count": 3,
        "last_commit_date": "2024-05-01T21:03:44Z",
        "has_readme": True,
        "topics": ["react", "typescript", "weather", "tailwindcss"],
        "homepage": "https://weather.janedoe.dev",
    }
    httpserver.check_assertions()


def test_execute_reports_has_readme_false_when_readme_missing(
    httpserver: HTTPServer, github_tool: GitHubTool
) -> None:
    """has_readme reflects the HEAD /readme result rather than being assumed."""
    register_repo(httpserver, load_fixture("repo_success"))
    register_readme(httpserver, status=404)

    result = github_tool.execute({"github_username": USERNAME, "repo_name": REPO_NAME})

    assert result.success is True
    assert result.data["has_readme"] is False
    httpserver.check_assertions()


def test_execute_sends_authorization_header_when_token_provided(
    httpserver: HTTPServer,
) -> None:
    """An api_token is forwarded as a GitHub token Authorization header."""
    httpserver.expect_request(
        f"/repos/{USERNAME}/{REPO_NAME}",
        method="GET",
        headers={"Authorization": "token secret-token"},
    ).respond_with_json(load_fixture("repo_success"))
    register_readme(httpserver, status=200)

    tool = GitHubTool(api_token="secret-token", base_url=httpserver.url_for(""))
    result = tool.execute({"github_username": USERNAME, "repo_name": REPO_NAME})

    assert result.success is True
    httpserver.check_assertions()


def test_execute_returns_not_found_on_404(httpserver: HTTPServer, github_tool: GitHubTool) -> None:
    """A 404 is surfaced as a friendly error rather than raising."""
    register_repo(httpserver, load_fixture("repo_not_found"), status=404)

    result = github_tool.execute({"github_username": USERNAME, "repo_name": REPO_NAME})

    assert result.success is False
    assert result.data == {}
    assert result.error == "Repository not found"
    httpserver.check_assertions()


def test_execute_returns_rate_limited_on_403(
    httpserver: HTTPServer, github_tool: GitHubTool
) -> None:
    """A 403 is reported as rate limiting / access denial."""
    register_repo(httpserver, load_fixture("rate_limited"), status=403)

    result = github_tool.execute({"github_username": USERNAME, "repo_name": REPO_NAME})

    assert result.success is False
    assert result.data == {}
    assert result.error == "Rate limited or access denied"
    httpserver.check_assertions()


def test_execute_reports_status_code_for_other_http_errors(
    httpserver: HTTPServer, github_tool: GitHubTool
) -> None:
    """Statuses with no dedicated branch fall back to the generic message."""
    register_repo(httpserver, {"message": "Server Error"}, status=500)

    result = github_tool.execute({"github_username": USERNAME, "repo_name": REPO_NAME})

    assert result.success is False
    assert result.error == "GitHub API error: 500"
    httpserver.check_assertions()


def test_execute_coalesces_null_fields(httpserver: HTTPServer, github_tool: GitHubTool) -> None:
    """Null description/language/homepage become the tool's documented defaults."""
    null_repo = "scratch-repo"
    register_repo(httpserver, load_fixture("repo_null_fields"), repo_name=null_repo)
    register_readme(httpserver, status=404, repo_name=null_repo)

    result = github_tool.execute({"github_username": USERNAME, "repo_name": null_repo})

    assert result.success is True
    assert result.data["description"] == ""
    assert result.data["primary_language"] == "Unknown"
    assert result.data["homepage"] == ""
    assert result.data["topics"] == []
    httpserver.check_assertions()


@pytest.mark.parametrize(
    "input_data",
    [
        {},
        {"github_username": USERNAME},
        {"repo_name": REPO_NAME},
        {"github_username": "", "repo_name": REPO_NAME},
        {"github_username": USERNAME, "repo_name": None},
    ],
)
def test_execute_rejects_missing_input_without_calling_api(
    httpserver: HTTPServer, github_tool: GitHubTool, input_data: dict
) -> None:
    """Incomplete input short-circuits before any HTTP request is made."""
    result = github_tool.execute(input_data)

    assert result.success is False
    assert result.data == {}
    assert result.error == "Missing github_username or repo_name"
    # No routes were registered, so any outbound request would show up here.
    httpserver.check_assertions()
    assert httpserver.log == []


def test_base_url_defaults_to_public_github_api() -> None:
    """Production callers keep hitting the real API when no base_url is passed."""
    assert GitHubTool().base_url == "https://api.github.com"


def test_base_url_trailing_slash_is_normalized() -> None:
    """url_for("") ends in a slash; the tool must not build //repos/... paths."""
    assert GitHubTool(base_url="http://localhost:8000/").base_url == "http://localhost:8000"
