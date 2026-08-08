"""Integration tests for GitHubTool, backed by a local pytest-httpserver mock.

Uses fixture responses in tests/fixtures/github_responses/ instead of the
live GitHub API, so these tests run deterministically without network
access or GitHub's rate limits. See issue #57.
"""

import json
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from agent.tools.github_tool import GitHubTool

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "github_responses"


def _load_fixture(name: str) -> dict:
    return dict(json.loads((FIXTURES_DIR / name).read_text()))


@pytest.mark.integration
def test_fetches_repo_metadata_successfully(httpserver: HTTPServer) -> None:
    repo_data = _load_fixture("repo_success.json")
    httpserver.expect_request("/repos/octocat/Hello-World").respond_with_json(repo_data)
    httpserver.expect_request("/repos/octocat/Hello-World/readme").respond_with_data(status=200)

    tool = GitHubTool(base_url=httpserver.url_for(""))
    result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

    assert result.success
    assert result.data["name"] == "Hello-World"
    assert result.data["primary_language"] == "Python"
    assert result.data["star_count"] == 42
    assert result.data["has_readme"] is True


@pytest.mark.integration
def test_repo_without_readme_reports_has_readme_false(httpserver: HTTPServer) -> None:
    repo_data = _load_fixture("repo_success.json")
    httpserver.expect_request("/repos/octocat/Hello-World").respond_with_json(repo_data)
    httpserver.expect_request("/repos/octocat/Hello-World/readme").respond_with_data(status=404)

    tool = GitHubTool(base_url=httpserver.url_for(""))
    result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

    assert result.success
    assert result.data["has_readme"] is False


@pytest.mark.integration
def test_repo_not_found_returns_error(httpserver: HTTPServer) -> None:
    error_body = _load_fixture("repo_not_found.json")
    httpserver.expect_request("/repos/octocat/Nonexistent").respond_with_json(
        error_body, status=404
    )

    tool = GitHubTool(base_url=httpserver.url_for(""))
    result = tool.execute({"github_username": "octocat", "repo_name": "Nonexistent"})

    assert not result.success
    assert result.error == "Repository not found"


@pytest.mark.integration
def test_rate_limited_returns_error(httpserver: HTTPServer) -> None:
    error_body = _load_fixture("rate_limited.json")
    httpserver.expect_request("/repos/octocat/Hello-World").respond_with_json(
        error_body, status=403
    )

    tool = GitHubTool(base_url=httpserver.url_for(""))
    result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

    assert not result.success
    assert result.error == "Rate limited or access denied"


@pytest.mark.integration
def test_malformed_json_response_returns_error(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/repos/octocat/Hello-World").respond_with_data(
        "not valid json{", content_type="application/json"
    )

    tool = GitHubTool(base_url=httpserver.url_for(""))
    result = tool.execute({"github_username": "octocat", "repo_name": "Hello-World"})

    assert not result.success
    assert result.error
