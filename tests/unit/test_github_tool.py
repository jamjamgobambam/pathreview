"""Tests for GitHubTool repo metadata, including the `has_tests` field (issue #50).

Issue: https://github.com/ascherj/pathreview/issues/50

`GitHubTool._fetch_repo_metadata` reports `has_readme`; issue #50 adds a `has_tests`
boolean computed from the repository tree (a `tests/`/`test/` directory, a
`pytest.ini`, or any `test_*.py` file). These tests mock the GitHub API so they run
offline. `test_repo_metadata_includes_has_tests` originally reproduced the gap (the
field was absent); it now passes with the field present.
"""

from unittest.mock import MagicMock, patch

import pytest

from agent.tools.github_tool import GitHubTool


def _repo_response(default_branch: str = "main") -> MagicMock:
    """Fake GitHub /repos/{u}/{r} response."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(
        return_value={
            "name": "demo",
            "description": "A demo repo",
            "language": "Python",
            "stargazers_count": 3,
            "forks_count": 1,
            "open_issues_count": 0,
            "pushed_at": "2026-01-01T00:00:00Z",
            "topics": [],
            "homepage": "",
            "default_branch": default_branch,
        }
    )
    return resp


def _tree_response(paths: list[tuple[str, str]]) -> MagicMock:
    """Fake git-tree response from a list of (path, type) tuples."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(
        return_value={"tree": [{"path": p, "type": t} for p, t in paths], "truncated": False}
    )
    return resp


def _head_ok() -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    return resp


@pytest.mark.unit
class TestGitHubToolHasTests:
    """Coverage for the `has_tests` repo-analysis field (issue #50)."""

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_repo_metadata_includes_has_tests(self, mock_get, mock_head):
        """Repo metadata must include a boolean `has_tests` field (issue #50)."""
        mock_get.side_effect = [_repo_response(), _tree_response([])]
        mock_head.return_value = _head_ok()

        result = GitHubTool().execute({"github_username": "octocat", "repo_name": "demo"})

        assert result.success is True
        assert "has_tests" in result.data
        assert isinstance(result.data["has_tests"], bool)

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_has_tests_true_for_tests_directory(self, mock_get, mock_head):
        mock_get.side_effect = [
            _repo_response(),
            _tree_response([("src", "tree"), ("tests", "tree"), ("tests/test_x.py", "blob")]),
        ]
        mock_head.return_value = _head_ok()
        result = GitHubTool().execute({"github_username": "u", "repo_name": "r"})
        assert result.data["has_tests"] is True

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_has_tests_true_for_singular_test_directory(self, mock_get, mock_head):
        mock_get.side_effect = [_repo_response(), _tree_response([("test", "tree")])]
        mock_head.return_value = _head_ok()
        result = GitHubTool().execute({"github_username": "u", "repo_name": "r"})
        assert result.data["has_tests"] is True

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_has_tests_true_for_pytest_ini(self, mock_get, mock_head):
        mock_get.side_effect = [_repo_response(), _tree_response([("pytest.ini", "blob")])]
        mock_head.return_value = _head_ok()
        result = GitHubTool().execute({"github_username": "u", "repo_name": "r"})
        assert result.data["has_tests"] is True

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_has_tests_true_for_test_py_file(self, mock_get, mock_head):
        mock_get.side_effect = [
            _repo_response(),
            _tree_response([("app.py", "blob"), ("test_app.py", "blob")]),
        ]
        mock_head.return_value = _head_ok()
        result = GitHubTool().execute({"github_username": "u", "repo_name": "r"})
        assert result.data["has_tests"] is True

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_has_tests_false_when_no_markers(self, mock_get, mock_head):
        mock_get.side_effect = [
            _repo_response(),
            _tree_response([("app.py", "blob"), ("README.md", "blob"), ("src", "tree")]),
        ]
        mock_head.return_value = _head_ok()
        result = GitHubTool().execute({"github_username": "u", "repo_name": "r"})
        assert result.data["has_tests"] is False

    @patch("agent.tools.github_tool.httpx.head")
    @patch("agent.tools.github_tool.httpx.get")
    def test_has_tests_false_on_tree_api_error(self, mock_get, mock_head):
        import httpx

        mock_get.side_effect = [_repo_response(), httpx.ConnectError("boom")]
        mock_head.return_value = _head_ok()
        result = GitHubTool().execute({"github_username": "u", "repo_name": "r"})
        # Metadata still returns; detection failure degrades to False, never raises.
        assert result.success is True
        assert result.data["has_tests"] is False
