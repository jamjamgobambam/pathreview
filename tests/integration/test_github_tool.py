"""Integration tests for GitHubTool against a mock GitHub API server.

These tests exercise ``agent.tools.github_tool.GitHubTool`` end-to-end without
touching live GitHub. A local ``pytest-httpserver`` instance answers requests
with pre-saved fixtures from ``tests/fixtures/github_responses/``.

The tool hardcodes ``base_url = "https://api.github.com"`` but exposes it as a
plain attribute, so each test points it at the mock via
``tool.base_url = httpserver.url_for("")``.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from pytest_httpserver import HTTPServer

from agent.tools.github_tool import GitHubTool

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "github_responses"

USERNAME = "octocat"
REPO = "hello-world"
REPO_PATH = f"/repos/{USERNAME}/{REPO}"
README_PATH = f"/repos/{USERNAME}/{REPO}/readme"


def load_fixture(name: str) -> dict[Any, Any]:
    """Load a JSON fixture from tests/fixtures/github_responses/.

    Args:
        name: Fixture filename, e.g. "repo_success.json".

    Returns:
        Parsed JSON as a dict.
    """
    result: dict[Any, Any] = json.loads((FIXTURES_DIR / name).read_text())
    return result


def fixture_status(response: dict[Any, Any]) -> int:
    """HTTP status for a fixture: its ``status`` field, or 200 if absent."""
    return int(response.get("status", 200))


@pytest.mark.integration
class TestGitHubTool:
    """Test suite for GitHubTool backed by a mock GitHub API server."""

    @pytest.fixture
    def tool(self, httpserver: HTTPServer) -> GitHubTool:
        """Return a GitHubTool pointed at the local mock server."""
        tool = GitHubTool()
        tool.base_url = httpserver.url_for("")
        return tool

    def test_execute_success_returns_full_metadata(
        self, tool: GitHubTool, httpserver: HTTPServer
    ) -> None:
        """Success path: full fixture maps to all metadata fields."""
        response = load_fixture("repo_success.json")
        httpserver.expect_request(REPO_PATH, method="GET").respond_with_json(
            response, status=fixture_status(response)
        )
        httpserver.expect_request(README_PATH, method="HEAD").respond_with_data("", status=200)

        result = tool.execute({"github_username": USERNAME, "repo_name": REPO})

        assert result.success is True
        assert result.error is None
        assert result.data == {
            "name": "pathreview",
            "description": "A code review tool",
            "primary_language": "Python",
            "star_count": 128,
            "fork_count": 12,
            "open_issues_count": 3,
            "last_commit_date": "2026-01-15T10:30:00Z",
            "has_readme": True,
            "topics": ["python", "fastapi", "ai"],
            "homepage": "https://pathreview.dev",
        }

    def test_execute_handles_null_fields_with_fallbacks(
        self, tool: GitHubTool, httpserver: HTTPServer
    ) -> None:
        """Null description/language/homepage and missing topics use fallbacks."""
        response = load_fixture("repo_nulls.json")
        httpserver.expect_request(REPO_PATH, method="GET").respond_with_json(
            response, status=fixture_status(response)
        )
        httpserver.expect_request(README_PATH, method="HEAD").respond_with_data("", status=200)

        result = tool.execute({"github_username": USERNAME, "repo_name": REPO})

        assert result.success is True
        assert result.data["description"] == ""
        assert result.data["primary_language"] == "Unknown"
        assert result.data["homepage"] == ""
        assert result.data["topics"] == []

    def test_execute_reports_readme_absent(self, tool: GitHubTool, httpserver: HTTPServer) -> None:
        """has_readme is False when the README HEAD request is not 200."""
        response = load_fixture("repo_success.json")
        httpserver.expect_request(REPO_PATH, method="GET").respond_with_json(
            response, status=fixture_status(response)
        )
        httpserver.expect_request(README_PATH, method="HEAD").respond_with_data("", status=404)

        result = tool.execute({"github_username": USERNAME, "repo_name": REPO})

        assert result.success is True
        assert result.data["has_readme"] is False

    def test_execute_reports_readme_present(self, tool: GitHubTool, httpserver: HTTPServer) -> None:
        """has_readme is True when the README HEAD request returns 200."""
        response = load_fixture("repo_success.json")
        httpserver.expect_request(REPO_PATH, method="GET").respond_with_json(
            response, status=fixture_status(response)
        )
        httpserver.expect_request(README_PATH, method="HEAD").respond_with_data("", status=200)

        result = tool.execute({"github_username": USERNAME, "repo_name": REPO})

        assert result.success is True
        assert result.data["has_readme"] is True

    def test_execute_404_returns_repository_not_found(
        self, tool: GitHubTool, httpserver: HTTPServer
    ) -> None:
        """404 metadata response maps to 'Repository not found'."""
        response = load_fixture("error_404.json")
        httpserver.expect_request(REPO_PATH, method="GET").respond_with_json(
            response, status=fixture_status(response)
        )

        result = tool.execute({"github_username": USERNAME, "repo_name": REPO})

        assert result.success is False
        assert result.data == {}
        assert result.error == "Repository not found"

    def test_execute_403_returns_rate_limited(
        self, tool: GitHubTool, httpserver: HTTPServer
    ) -> None:
        """403 metadata response maps to 'Rate limited or access denied'."""
        response = load_fixture("error_403.json")
        httpserver.expect_request(REPO_PATH, method="GET").respond_with_json(
            response, status=fixture_status(response)
        )

        result = tool.execute({"github_username": USERNAME, "repo_name": REPO})

        assert result.success is False
        assert result.data == {}
        assert result.error == "Rate limited or access denied"

    def test_execute_generic_error_returns_status_message(
        self, tool: GitHubTool, httpserver: HTTPServer
    ) -> None:
        """Other status (e.g. 500) maps to 'GitHub API error: <code>'."""
        response = load_fixture("error_500.json")
        httpserver.expect_request(REPO_PATH, method="GET").respond_with_json(
            response, status=fixture_status(response)
        )

        result = tool.execute({"github_username": USERNAME, "repo_name": REPO})

        assert result.success is False
        assert result.data == {}
        assert result.error == "GitHub API error: 500"

    def test_execute_missing_username_returns_error(self, tool: GitHubTool) -> None:
        """Missing github_username fails without calling the server."""
        result = tool.execute({"repo_name": REPO})

        assert result.success is False
        assert result.data == {}
        assert result.error == "Missing github_username or repo_name"

    def test_execute_missing_repo_name_returns_error(self, tool: GitHubTool) -> None:
        """Missing repo_name fails without calling the server."""
        result = tool.execute({"github_username": USERNAME})

        assert result.success is False
        assert result.data == {}
        assert result.error == "Missing github_username or repo_name"
