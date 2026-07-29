"""Tests for GitHub repository metadata analysis."""

from unittest.mock import Mock, patch

import pytest

from agent.tools.base import ToolResult
from agent.tools.github_tool import GitHubTool


@pytest.mark.unit
class TestGitHubTool:
    """Test GitHub repository test-presence metadata."""

    @staticmethod
    def _execute_with_tree(
        tree: object,
        *,
        default_branch: str = "main",
        truncated: bool = False,
    ) -> tuple[ToolResult, Mock]:
        """Execute the tool with mocked repository and tree responses."""
        repo_response = Mock()
        repo_response.raise_for_status.return_value = None
        repo_response.json.return_value = {
            "name": "portfolio-project",
            "description": "A project with tests",
            "language": "Python",
            "default_branch": default_branch,
        }

        tree_response = Mock()
        tree_response.raise_for_status.return_value = None
        tree_response.json.return_value = {
            "tree": tree,
            "truncated": truncated,
        }

        def get_response(url: str, **_kwargs: object) -> Mock:
            if "/git/trees/" in url:
                return tree_response
            return repo_response

        with (
            patch("agent.tools.github_tool.httpx.get", side_effect=get_response) as mock_get,
            patch("agent.tools.github_tool.httpx.head") as mock_head,
        ):
            mock_head.return_value.status_code = 200
            result = GitHubTool().execute(
                {"github_username": "example-user", "repo_name": "portfolio-project"}
            )

        return result, mock_get

    @pytest.mark.parametrize(
        ("path", "entry_type"),
        [
            ("tests", "tree"),
            ("tests/.gitkeep", "blob"),
            ("src/test/test_api.py", "blob"),
            ("pytest.ini", "blob"),
            ("config/pytest.ini", "blob"),
            ("test_example.py", "blob"),
            ("src/test_api.py", "blob"),
        ],
    )
    def test_supported_indicator_reports_has_tests(self, path: str, entry_type: str) -> None:
        """Each supported directory or file indicator should report True."""
        result, _ = self._execute_with_tree([{"path": path, "type": entry_type}])

        assert result.success is True
        assert result.data["has_tests"] is True

    @pytest.mark.parametrize(
        "path",
        [
            "contest/example.py",
            "testing/example.py",
            "pytest.ini.example",
            "test_helper.js",
            "helper_test.py",
            "Tests/example.py",
        ],
    )
    def test_near_match_does_not_report_has_tests(self, path: str) -> None:
        """Unsupported near matches should not create false positives."""
        result, _ = self._execute_with_tree([{"path": path, "type": "blob"}])

        assert result.success is True
        assert result.data["has_tests"] is False

    def test_empty_tree_reports_has_tests_false(self) -> None:
        """A complete tree without indicators should report False."""
        result, _ = self._execute_with_tree([])

        assert result.success is True
        assert result.data["has_tests"] is False

    def test_default_branch_is_url_encoded(self) -> None:
        """Branch names containing slashes should be safe in the tree URL."""
        result, mock_get = self._execute_with_tree([], default_branch="release/next")

        assert result.success is True
        mock_get.assert_any_call(
            "https://api.github.com/repos/example-user/portfolio-project/"
            "git/trees/release%2Fnext?recursive=1",
            headers={},
            timeout=10.0,
        )

    def test_truncated_tree_returns_analysis_error(self) -> None:
        """An incomplete recursive tree must not report a confident False."""
        result, _ = self._execute_with_tree([], truncated=True)

        assert result.success is False
        assert result.data == {}
        assert result.error == "GitHub repository tree is unavailable or truncated"

    def test_malformed_tree_returns_analysis_error(self) -> None:
        """A malformed tree payload should follow the tool's error contract."""
        result, _ = self._execute_with_tree("not-a-list")

        assert result.success is False
        assert result.data == {}
        assert result.error == "GitHub repository tree response is malformed"
