"""Tests for github_tool.py"""

from unittest.mock import Mock, patch

import pytest

from agent.tools.github_tool import GitHubTool


@pytest.mark.unit
class TestGitHubTool:
    """Test suite for GitHubTool."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        """Create a GitHubTool instance."""
        return GitHubTool()

    def _mock_response(self, json_data: dict, status_code: int = 200) -> Mock:
        """Build a mock httpx.Response-like object."""
        response = Mock()
        response.status_code = status_code
        response.json.return_value = json_data
        response.raise_for_status = Mock()
        return response

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_has_tests_true_when_test_directory_present(
        self, mock_get: Mock, mock_head: Mock, tool: GitHubTool
    ) -> None:
        """Test has_tests is True when repo tree contains a tests/ directory."""
        repo_response = self._mock_response(
            {
                "name": "example-repo",
                "description": "An example",
                "language": "Python",
                "stargazers_count": 10,
                "forks_count": 2,
                "open_issues_count": 1,
                "pushed_at": "2026-01-01T00:00:00Z",
                "topics": [],
                "homepage": "",
                "default_branch": "main",
            }
        )
        tree_response = self._mock_response(
            {
                "tree": [
                    {"path": "src/main.py"},
                    {"path": "tests/test_main.py"},
                ],
                "truncated": False,
            }
        )
        head_response = Mock()
        head_response.status_code = 200
        mock_head.return_value = head_response

        mock_get.side_effect = [repo_response, tree_response]

        result = tool.execute({"github_username": "someuser", "repo_name": "example-repo"})

        assert result.success is True
        assert "tests/test_main.py" in result.data["file_structure"]

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_file_structure_empty_when_tree_fetch_fails(
        self, mock_get: Mock, mock_head: Mock, tool: GitHubTool
    ) -> None:
        """Test file_structure gracefully falls back to empty string on API failure."""
        repo_response = self._mock_response(
            {
                "name": "example-repo",
                "description": "",
                "language": "Python",
                "stargazers_count": 0,
                "forks_count": 0,
                "open_issues_count": 0,
                "pushed_at": "",
                "topics": [],
                "homepage": "",
                "default_branch": "main",
            }
        )
        head_response = Mock()
        head_response.status_code = 200
        mock_head.return_value = head_response

        mock_get.side_effect = [repo_response, Exception("network error")]

        result = tool.execute({"github_username": "someuser", "repo_name": "example-repo"})

        assert result.success is True
        assert result.data["file_structure"] == ""

    @patch("agent.tools.github_tool.httpx.get")
    def test_missing_username_or_repo_returns_error(self, mock_get: Mock, tool: GitHubTool) -> None:
        """Test execute() fails gracefully when required input is missing."""
        result = tool.execute({"github_username": "someuser"})

        assert result.success is False
        assert result.error is not None
        assert "Missing" in result.error
        mock_get.assert_not_called()
