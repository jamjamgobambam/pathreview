"""Tests for github_tool.py."""

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

    def test_has_tests_detects_tests_directory(self, tool: GitHubTool) -> None:
        """Return True when the repository contains a tests directory."""
        paths = [
            "README.md",
            "src/app.py",
            "tests/test_app.py",
        ]

        assert tool._has_tests(paths) is True

    def test_has_tests_returns_false_without_test_indicators(self, tool: GitHubTool) -> None:
        """Return False when the repository contains no recognized tests."""
        paths = [
            "README.md",
            "src/app.py",
            "requirements.txt",
        ]

        assert tool._has_tests(paths) is False

    def test_has_tests_detects_python_test_file(self, tool: GitHubTool) -> None:
        """Return True when a test_*.py file exists."""
        paths = [
            "README.md",
            "src/app.py",
            "test_app.py",
        ]

        assert tool._has_tests(paths) is True

    def test_has_tests_detects_pytest_config(self, tool: GitHubTool) -> None:
        """Return True when pytest.ini exists."""
        paths = [
            "README.md",
            "src/app.py",
            "pytest.ini",
        ]

        assert tool._has_tests(paths) is True

    def test_has_tests_ignores_unrelated_filenames(self, tool: GitHubTool) -> None:
        """Return False for filenames that only contain similar text."""
        paths = [
            "README.md",
            "latest_update.py",
            "contest_results.py",
            "testing_notes.md",
        ]

        assert tool._has_tests(paths) is False

    @patch("agent.tools.github_tool.httpx.get")
    def test_fetch_repo_tree_returns_repository_paths(
        self, mock_get: Mock, tool: GitHubTool
    ) -> None:
        """Return repository paths from the GitHub tree response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tree": [
                {"path": "README.md", "type": "blob"},
                {"path": "src", "type": "tree"},
                {"path": "src/app.py", "type": "blob"},
                {"path": "tests/test_app.py", "type": "blob"},
            ],
            "truncated": False,
        }
        mock_get.return_value = mock_response

        paths = tool._fetch_repo_tree("octocat", "sample-repo", "main")

        assert paths == [
            "README.md",
            "src",
            "src/app.py",
            "tests/test_app.py",
        ]

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_repo_metadata_includes_has_tests(
        self,
        mock_get: Mock,
        mock_head: Mock,
        tool: GitHubTool,
    ) -> None:
        """Include has_tests in repository metadata."""
        repo_response = Mock()
        repo_response.json.return_value = {
            "name": "sample-repo",
            "description": "Sample repository",
            "language": "Python",
            "stargazers_count": 5,
            "forks_count": 2,
            "open_issues_count": 1,
            "pushed_at": "2026-07-30T12:00:00Z",
            "default_branch": "develop",
            "topics": [],
            "homepage": None,
        }

        tree_response = Mock()
        tree_response.json.return_value = {
            "tree": [
                {"path": "README.md", "type": "blob"},
                {"path": "tests/test_app.py", "type": "blob"},
            ],
            "truncated": False,
        }

        mock_get.side_effect = [repo_response, tree_response]
        mock_head.return_value.status_code = 200

        metadata = tool._fetch_repo_metadata("octocat", "sample-repo")

        tree_request = mock_get.call_args_list[1]
        assert "/git/trees/develop" in tree_request.args[0]
        assert metadata["has_tests"] is True
