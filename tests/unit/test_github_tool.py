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

    def test_fetch_file_structure_returns_joined_paths(self, tool: GitHubTool) -> None:
        """When the API returns a file tree, paths are flattened into a
        newline-joined string, matching the format repo_analyzer.py expects."""
        with patch("agent.tools.github_tool.httpx.get") as mock_get:
            mock_repo_response = Mock()
            mock_repo_response.json.return_value = {"default_branch": "main"}
            mock_repo_response.raise_for_status.return_value = None

            mock_tree_response = Mock()
            mock_tree_response.json.return_value = {
                "truncated": False,
                "tree": [
                    {"path": "README.md"},
                    {"path": "tests/test_example.py"},
                    {"path": "src/main.py"},
                ],
            }
            mock_tree_response.raise_for_status.return_value = None

            mock_get.side_effect = [mock_repo_response, mock_tree_response]

            result = tool._fetch_file_structure("someuser", "somerepo")

            assert result == "README.md\ntests/test_example.py\nsrc/main.py"

    def test_fetch_file_structure_returns_empty_string_on_failure(self, tool: GitHubTool) -> None:
        """When the API call fails, _fetch_file_structure degrades gracefully
        and returns an empty string rather than raising."""
        with patch("agent.tools.github_tool.httpx.get") as mock_get:
            mock_get.side_effect = Exception("API error")

            result = tool._fetch_file_structure("someuser", "somerepo")

            assert result == ""

    def test_fetch_file_structure_logs_warning_on_truncated_tree(self, tool: GitHubTool) -> None:
        """When GitHub reports the tree as truncated, a warning is logged
        but the method still returns whatever paths were included."""
        with (
            patch("agent.tools.github_tool.httpx.get") as mock_get,
            patch("agent.tools.github_tool.logger") as mock_logger,
        ):
            mock_repo_response = Mock()
            mock_repo_response.json.return_value = {"default_branch": "main"}
            mock_repo_response.raise_for_status.return_value = None

            mock_tree_response = Mock()
            mock_tree_response.json.return_value = {
                "truncated": True,
                "tree": [{"path": "README.md"}],
            }
            mock_tree_response.raise_for_status.return_value = None

            mock_get.side_effect = [mock_repo_response, mock_tree_response]

            result = tool._fetch_file_structure("someuser", "somerepo")

            assert result == "README.md"
            mock_logger.warning.assert_called_once()

    def test_fetch_repo_metadata_includes_file_structure_key(self, tool: GitHubTool) -> None:
        """The metadata dict returned by _fetch_repo_metadata includes the
        new file_structure field alongside existing fields."""
        with (
            patch("agent.tools.github_tool.httpx.get") as mock_get,
            patch("agent.tools.github_tool.httpx.head") as mock_head,
        ):
            mock_repo_json_response = Mock()
            mock_repo_json_response.json.return_value = {
                "name": "somerepo",
                "description": "A test repo",
                "language": "Python",
                "stargazers_count": 5,
                "forks_count": 1,
                "open_issues_count": 0,
                "pushed_at": "2026-01-01T00:00:00Z",
                "topics": [],
                "homepage": "",
                "default_branch": "main",
            }
            mock_repo_json_response.raise_for_status.return_value = None

            mock_tree_response = Mock()
            mock_tree_response.json.return_value = {
                "truncated": False,
                "tree": [{"path": "tests/test_example.py"}],
            }
            mock_tree_response.raise_for_status.return_value = None

            # First call: main metadata fetch. Second/third: file structure fetch
            # (repo lookup for default_branch, then tree lookup).
            mock_get.side_effect = [
                mock_repo_json_response,
                mock_repo_json_response,
                mock_tree_response,
            ]

            mock_head_response = Mock()
            mock_head_response.status_code = 200
            mock_head.return_value = mock_head_response

            metadata = tool._fetch_repo_metadata("someuser", "somerepo")

            assert "file_structure" in metadata
            assert metadata["file_structure"] == "tests/test_example.py"
