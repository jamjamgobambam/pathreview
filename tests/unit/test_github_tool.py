"""Tests for github_tool.py

Coverage for issue #50: "Add a `has_tests` boolean to the repo analysis output"
(https://github.com/ascherj/pathreview/issues/50).

`GitHubTool` assembles repository metadata in `_fetch_repo_metadata`. These tests
verify that the output now exposes a `has_tests` boolean and that the underlying
`_has_tests` detection correctly recognizes a `tests/`/`test/` directory, a
`pytest.ini`, or `test_*.py` files, while degrading gracefully on API failure.
All outbound HTTP is mocked, so no network access is required.
"""

from typing import Any

import pytest

from agent.tools import github_tool as github_tool_module
from agent.tools.github_tool import GitHubTool


class _FakeResponse:
    """Minimal stand-in for an httpx.Response."""

    def __init__(
        self,
        status_code: int = 200,
        json_data: dict | None = None,
        raise_exc: bool = False,
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data or {}
        self._raise_exc = raise_exc

    def json(self) -> dict:
        return self._json_data

    def raise_for_status(self) -> None:
        if self._raise_exc:
            raise RuntimeError("simulated GitHub API error")


REPO_JSON = {
    "name": "portfolio-project",
    "description": "A sample project",
    "language": "Python",
    "stargazers_count": 12,
    "forks_count": 3,
    "open_issues_count": 1,
    "pushed_at": "2026-01-01T00:00:00Z",
    "default_branch": "main",
    "topics": ["python", "portfolio"],
    "homepage": "",
}


def _build_tool(
    monkeypatch: pytest.MonkeyPatch,
    tree: list[dict] | None = None,
    tree_ok: bool = True,
) -> GitHubTool:
    """Build a GitHubTool with httpx stubbed to serve a given repo tree.

    Args:
        monkeypatch: pytest fixture used to patch the httpx module.
        tree: Entries returned by the mocked Git Trees API (each a dict with
            ``path`` and ``type``). Defaults to an empty tree.
        tree_ok: When False, the mocked Git Trees request fails, exercising the
            graceful-degradation path.
    """
    tree = tree or []

    def fake_get(
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        timeout: float | None = None,
    ) -> _FakeResponse:
        if "/git/trees/" in url:
            if not tree_ok:
                return _FakeResponse(500, raise_exc=True)
            return _FakeResponse(200, {"tree": tree, "truncated": False})
        return _FakeResponse(200, REPO_JSON)

    def fake_head(
        url: str, headers: dict | None = None, timeout: float | None = None
    ) -> _FakeResponse:
        return _FakeResponse(200)

    monkeypatch.setattr(github_tool_module.httpx, "get", fake_get)
    monkeypatch.setattr(github_tool_module.httpx, "head", fake_head)
    return GitHubTool()


def _run(tool: GitHubTool) -> dict[str, Any]:
    result = tool.execute({"github_username": "octocat", "repo_name": "portfolio-project"})
    assert result.success is True
    return result.data


@pytest.mark.unit
class TestGitHubToolHasTests:
    """Behavior of the has_tests field and its detection (issue #50)."""

    def test_output_includes_has_tests_field(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The analysis output exposes a has_tests boolean (reproduction of #50)."""
        data = _run(_build_tool(monkeypatch, tree=[{"path": "README.md", "type": "blob"}]))
        assert "has_tests" in data
        assert isinstance(data["has_tests"], bool)

    def test_detects_tests_directory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A tests/ directory sets has_tests True."""
        tree = [{"path": "tests", "type": "tree"}, {"path": "main.py", "type": "blob"}]
        assert _run(_build_tool(monkeypatch, tree=tree))["has_tests"] is True

    def test_detects_singular_test_directory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A test/ directory (singular) also counts."""
        tree = [{"path": "test", "type": "tree"}]
        assert _run(_build_tool(monkeypatch, tree=tree))["has_tests"] is True

    def test_detects_nested_tests_directory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A tests/ directory nested under a package still counts."""
        tree = [{"path": "src/pkg/tests", "type": "tree"}]
        assert _run(_build_tool(monkeypatch, tree=tree))["has_tests"] is True

    def test_detects_pytest_ini(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A pytest.ini with no tests/ dir still sets has_tests True."""
        tree = [{"path": "pytest.ini", "type": "blob"}, {"path": "app.py", "type": "blob"}]
        assert _run(_build_tool(monkeypatch, tree=tree))["has_tests"] is True

    def test_detects_test_py_file_at_any_depth(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A test_*.py file anywhere in the tree sets has_tests True."""
        tree = [{"path": "src/deep/test_math.py", "type": "blob"}]
        assert _run(_build_tool(monkeypatch, tree=tree))["has_tests"] is True

    def test_no_tests_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A repo with no test signals reports has_tests False."""
        tree = [
            {"path": "main.py", "type": "blob"},
            {"path": "README.md", "type": "blob"},
            {"path": "src", "type": "tree"},
        ]
        assert _run(_build_tool(monkeypatch, tree=tree))["has_tests"] is False

    def test_similar_names_not_falsely_matched(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Files like contest.py or latest_run.py must not count as tests."""
        tree = [
            {"path": "contest.py", "type": "blob"},
            {"path": "latest_run.py", "type": "blob"},
            {"path": "attest.py", "type": "blob"},
        ]
        assert _run(_build_tool(monkeypatch, tree=tree))["has_tests"] is False

    def test_api_failure_degrades_to_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If the Git Trees request fails, has_tests is False and the tool still succeeds."""
        data = _run(_build_tool(monkeypatch, tree_ok=False))
        assert data["has_tests"] is False


@pytest.mark.unit
class TestTreeHasTests:
    """Unit tests for the pure _tree_has_tests helper."""

    def test_empty_tree(self) -> None:
        assert GitHubTool._tree_has_tests([]) is False

    def test_matches_test_prefix_only(self) -> None:
        assert GitHubTool._tree_has_tests([{"path": "test_x.py", "type": "blob"}]) is True
        assert GitHubTool._tree_has_tests([{"path": "latest.py", "type": "blob"}]) is False

    def test_directory_must_be_tree_type(self) -> None:
        # A blob literally named "tests" (not a directory) should not count.
        assert GitHubTool._tree_has_tests([{"path": "tests", "type": "blob"}]) is False
        assert GitHubTool._tree_has_tests([{"path": "tests", "type": "tree"}]) is True
