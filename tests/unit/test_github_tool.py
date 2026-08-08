"""Tests for github_tool.py"""

import pytest

from agent.tools.github_tool import GitHubTool


@pytest.mark.unit
class TestGitHubTool:
    """Test suite for GitHubTool."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        """Create a GitHubTool instance."""
        return GitHubTool()

    def test_default_base_url_is_real_github_api(self, tool: GitHubTool) -> None:
        """Test base_url defaults to the real GitHub API when not overridden."""
        assert tool.base_url == "https://api.github.com"

    def test_custom_base_url_is_stored(self) -> None:
        """Test base_url can be overridden, e.g. to point at a mock server."""
        tool = GitHubTool(base_url="http://localhost:8000")

        assert tool.base_url == "http://localhost:8000"

    def test_missing_username_returns_error(self, tool: GitHubTool) -> None:
        """Test execute fails fast when github_username is missing."""
        result = tool.execute({"repo_name": "Hello-World"})

        assert not result.success
        assert result.error == "Missing github_username or repo_name"

    def test_missing_repo_name_returns_error(self, tool: GitHubTool) -> None:
        """Test execute fails fast when repo_name is missing."""
        result = tool.execute({"github_username": "octocat"})

        assert not result.success
        assert result.error == "Missing github_username or repo_name"

    def test_missing_both_fields_returns_error(self, tool: GitHubTool) -> None:
        """Test execute fails fast when both required fields are missing."""
        result = tool.execute({})

        assert not result.success
        assert result.error == "Missing github_username or repo_name"
