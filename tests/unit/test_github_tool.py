"""Tests for github_tool.py"""

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from agent.tools.base import ToolResult
from agent.tools.github_tool import GitHubTool

REPO_JSON = {
    "name": "sample-repo",
    "description": "A sample repo",
    "language": "Python",
    "stargazers_count": 5,
    "forks_count": 1,
    "open_issues_count": 0,
    "pushed_at": "2026-01-01T00:00:00Z",
    "topics": [],
    "homepage": "",
    "default_branch": "main",
}


def _make_get_mock(
    tree_entries: list[dict] | None = None,
    tree_raises: bool = False,
    truncated: bool = False,
) -> Callable[..., MagicMock]:
    """Fake httpx.get that returns repo metadata or a tree listing
    depending on the requested URL, matching GitHubTool's real call shape.
    """

    def fake_get(url: str, *args: object, **kwargs: object) -> MagicMock:
        if "/git/trees/" in url:
            if tree_raises:
                raise Exception("boom")
            response = MagicMock()
            response.raise_for_status.return_value = None
            response.json.return_value = {
                "tree": tree_entries or [],
                "truncated": truncated,
            }
            return response

        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = REPO_JSON
        return response

    return fake_get


@pytest.mark.unit
class TestGitHubToolHasTests:
    """Tests for issue #50: has_tests detection on GitHubTool."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        return GitHubTool()

    def _run(
        self,
        tool: GitHubTool,
        monkeypatch: pytest.MonkeyPatch,
        tree_entries: list[dict] | None = None,
        tree_raises: bool = False,
        truncated: bool = False,
    ) -> ToolResult:
        monkeypatch.setattr("httpx.get", _make_get_mock(tree_entries, tree_raises, truncated))
        monkeypatch.setattr("httpx.head", lambda *a, **k: MagicMock(status_code=200))
        return tool.execute({"github_username": "octocat", "repo_name": "sample-repo"})

    def test_has_tests_true_for_tests_directory(
        self, tool: GitHubTool, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A tests/ directory anywhere in the tree should be detected."""
        entries = [
            {"path": "main.py", "type": "blob"},
            {"path": "tests", "type": "tree"},
            {"path": "tests/test_main.py", "type": "blob"},
        ]
        result = self._run(tool, monkeypatch, tree_entries=entries)
        assert result.success is True
        assert result.data["has_tests"] is True

    def test_has_tests_true_for_nested_test_directory(
        self, tool: GitHubTool, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A test/ directory nested under a subfolder should still count."""
        entries = [{"path": "backend/test", "type": "tree"}]
        result = self._run(tool, monkeypatch, tree_entries=entries)
        assert result.data["has_tests"] is True

    def test_has_tests_true_for_pytest_ini(
        self, tool: GitHubTool, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A pytest.ini file with no dedicated tests/ dir should count."""
        entries = [
            {"path": "pytest.ini", "type": "blob"},
            {"path": "main.py", "type": "blob"},
        ]
        result = self._run(tool, monkeypatch, tree_entries=entries)
        assert result.data["has_tests"] is True

    def test_has_tests_true_for_test_prefixed_file(
        self, tool: GitHubTool, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A loose test_*.py file with no tests/ dir or pytest.ini should count."""
        entries = [{"path": "src/test_utils.py", "type": "blob"}]
        result = self._run(tool, monkeypatch, tree_entries=entries)
        assert result.data["has_tests"] is True

    def test_has_tests_false_when_no_signals_present(
        self, tool: GitHubTool, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A repo with no test-related paths should report False, not missing."""
        entries = [
            {"path": "main.py", "type": "blob"},
            {"path": "README.md", "type": "blob"},
        ]
        result = self._run(tool, monkeypatch, tree_entries=entries)
        assert result.data["has_tests"] is False

    def test_has_tests_false_on_tree_api_error(
        self, tool: GitHubTool, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the tree API call fails, degrade to False rather than raising."""
        result = self._run(tool, monkeypatch, tree_raises=True)
        assert result.success is True
        assert result.data["has_tests"] is False

    def test_has_tests_does_not_special_case_truncated_response(
        self, tool: GitHubTool, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Known limitation, documented per code review on PR #221: GitHub
        sets `"truncated": true` on the tree response for very large repos,
        meaning some paths may be missing. _has_tests() does not currently
        read that flag -- it just evaluates whatever entries it received. If
        the actual tests/ directory happens to fall outside the truncated
        portion, this produces a false negative rather than an error. This
        test pins down that current behavior so a future change to it is a
        deliberate decision, not an accidental one.
        """
        entries = [
            {"path": "main.py", "type": "blob"},
            {"path": "README.md", "type": "blob"},
            # tests/ exists in the real repo but falls past the truncation
            # point, so it never appears in this (truncated) tree listing.
        ]
        result = self._run(tool, monkeypatch, tree_entries=entries, truncated=True)
        assert result.success is True
        assert result.data["has_tests"] is False
