"""Integration tests for GitHubTool, backed by the mock GitHub server."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    # NOTE: keep this in sync with the import in conftest.py
    from agent.tools.github_tool import GitHubTool


@pytest.mark.integration
def test_fetch_repo_success(github_tool: GitHubTool) -> None:
    result = github_tool.execute({"github_username": "octocat", "repo_name": "hello-world"})

    assert result.success is True
    assert result.data["name"] == "hello-world"
    assert result.data["primary_language"] == "Ruby"
    assert result.data["star_count"] == 80
    assert result.data["fork_count"] == 9
    assert result.data["has_readme"] is True
    assert result.data["topics"] == ["octocat", "atom", "electron", "api"]


@pytest.mark.integration
def test_fetch_repo_without_readme(github_tool: GitHubTool) -> None:
    result = github_tool.execute({"github_username": "octocat", "repo_name": "no-readme-repo"})

    assert result.success is True
    assert result.data["has_readme"] is False
    # null description/homepage should be coerced to ""
    assert result.data["description"] == ""
    assert result.data["homepage"] == ""


@pytest.mark.integration
def test_fetch_repo_not_found(github_tool: GitHubTool) -> None:
    result = github_tool.execute({"github_username": "octocat", "repo_name": "missing-repo"})

    assert result.success is False
    assert result.data == {}
    assert result.error == "Repository not found"


@pytest.mark.integration
def test_fetch_repo_rate_limited(github_tool: GitHubTool) -> None:
    result = github_tool.execute({"github_username": "octocat", "repo_name": "rate-limited-repo"})

    assert result.success is False
    assert result.error == "Rate limited or access denied"


@pytest.mark.integration
def test_missing_input_fields(github_tool: GitHubTool) -> None:
    result = github_tool.execute({"github_username": "octocat"})

    assert result.success is False
    assert result.error == "Missing github_username or repo_name"
