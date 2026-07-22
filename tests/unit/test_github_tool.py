"""Tests for GitHub repository metadata analysis."""

from unittest.mock import Mock, patch

import pytest

from agent.tools.github_tool import GitHubTool


@pytest.mark.unit
class TestGitHubTool:
    """Reproduce missing test-presence metadata from issue #50."""

    def test_repo_with_test_file_reports_has_tests(self) -> None:
        """A repository containing test_*.py should report has_tests=True."""
        repo_response = Mock()
        repo_response.raise_for_status.return_value = None
        repo_response.json.return_value = {
            "name": "portfolio-project",
            "description": "A project with tests",
            "language": "Python",
            "default_branch": "main",
        }

        tree_response = Mock()
        tree_response.raise_for_status.return_value = None
        tree_response.json.return_value = {
            "tree": [
                {"path": "app.py", "type": "blob"},
                {"path": "tests/test_example.py", "type": "blob"},
            ]
        }

        def get_response(url: str, **_kwargs: object) -> Mock:
            if url.endswith("/git/trees/main?recursive=1"):
                return tree_response
            return repo_response

        with (
            patch("agent.tools.github_tool.httpx.get", side_effect=get_response),
            patch("agent.tools.github_tool.httpx.head") as mock_head,
        ):
            mock_head.return_value.status_code = 200
            result = GitHubTool().execute(
                {"github_username": "example-user", "repo_name": "portfolio-project"}
            )

        assert result.success is True
        assert result.data["has_tests"] is True
