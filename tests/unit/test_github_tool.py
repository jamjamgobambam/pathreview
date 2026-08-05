"""Tests for agent/tools/github_tool.py.

Covers issue #50 (issue-catalog id C-10):
    "Add a has_tests boolean to the repo analysis output"
    https://github.com/ascherj/pathreview/issues/50

`GitHubTool` is the agent-side repo analysis tool named in the issue. Its
`_fetch_repo_metadata()` output reported `has_readme` but not `has_tests`.

`test_analysis_output_includes_has_tests` began as the reproduction for that gap
(it failed because the key was absent); it now serves as the regression guard
that the field is present and boolean. The remaining tests cover the detection
behaviour itself: which paths count as test markers, and that any failure
reading the repository file tree degrades to `False` rather than raising.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from agent.tools.base import ToolResult
from agent.tools.github_tool import GitHubTool

REPO_JSON = {
    "name": "example-repo",
    "description": "A test repository",
    "language": "Python",
    "stargazers_count": 42,
    "forks_count": 7,
    "open_issues_count": 3,
    "pushed_at": "2024-01-01T00:00:00Z",
    "default_branch": "main",
    "topics": ["python"],
    "homepage": "",
}


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Build a mock httpx response that returns ``json_data``."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


def _tree_response(paths: list[str], truncated: bool = False) -> MagicMock:
    """Build a mock Git Trees API response listing ``paths``."""
    return _mock_response(
        {
            "tree": [{"path": path, "type": "blob"} for path in paths],
            "truncated": truncated,
        }
    )


@pytest.mark.unit
class TestGitHubToolHasTests:
    """The agent repo analysis output exposes a has_tests boolean."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        return GitHubTool()

    def _execute(self, mock_httpx: MagicMock, tool: GitHubTool, tree: MagicMock) -> ToolResult:
        """Drive ``execute()`` with a mocked repo call followed by a tree call.

        ``_fetch_repo_metadata`` makes exactly two GET calls in a fixed order —
        the repo metadata first, then the file tree — because the keys of a dict
        literal are evaluated top to bottom. That is what lets side_effect hand
        back the two responses positionally.
        """
        mock_httpx.get.side_effect = [_mock_response(REPO_JSON), tree]

        # _has_readme probes with HEAD, not GET, so it is mocked separately and
        # does not consume one of the two GET responses above.
        head_response = MagicMock()
        head_response.status_code = 200
        mock_httpx.head.return_value = head_response

        return tool.execute({"github_username": "octocat", "repo_name": "example-repo"})

    @patch("agent.tools.github_tool.httpx")
    def test_analysis_output_includes_has_tests(
        self, mock_httpx: MagicMock, tool: GitHubTool
    ) -> None:
        # Mock the repository-metadata GET call.
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "name": "example-repo",
            "description": "A test repository",
            "language": "Python",
            "stargazers_count": 42,
            "forks_count": 7,
            "open_issues_count": 3,
            "pushed_at": "2024-01-01T00:00:00Z",
            "topics": ["python"],
            "homepage": "",
        }
        mock_get_response.raise_for_status.return_value = None
        mock_httpx.get.return_value = mock_get_response

        # Mock the README HEAD probe used by the existing _has_readme helper.
        mock_head_response = MagicMock()
        mock_head_response.status_code = 200
        mock_httpx.head.return_value = mock_head_response

        result = tool.execute({"github_username": "octocat", "repo_name": "example-repo"})

        assert result.success is True

        # Regression guard: the existing has_readme field should still be present.
        assert "has_readme" in result.data

        # Issue #50: the analysis output MUST expose a has_tests boolean.
        assert (
            "has_tests" in result.data
        ), "has_tests missing from GitHubTool analysis output — see issue #50"
        assert isinstance(result.data["has_tests"], bool)

    @patch("agent.tools.github_tool.httpx")
    def test_tests_directory_detected(self, mock_httpx: MagicMock, tool: GitHubTool) -> None:
        result = self._execute(mock_httpx, tool, _tree_response(["README.md", "tests/test_app.py"]))

        assert result.success is True
        assert result.data["has_tests"] is True

    @patch("agent.tools.github_tool.httpx")
    def test_scattered_test_file_detected(self, mock_httpx: MagicMock, tool: GitHubTool) -> None:
        result = self._execute(mock_httpx, tool, _tree_response(["app.py", "test_app.py"]))

        assert result.data["has_tests"] is True

    @patch("agent.tools.github_tool.httpx")
    def test_pytest_ini_detected(self, mock_httpx: MagicMock, tool: GitHubTool) -> None:
        result = self._execute(mock_httpx, tool, _tree_response(["app.py", "pytest.ini"]))

        assert result.data["has_tests"] is True

    @patch("agent.tools.github_tool.httpx")
    def test_repo_without_tests_reports_false(
        self, mock_httpx: MagicMock, tool: GitHubTool
    ) -> None:
        result = self._execute(
            mock_httpx, tool, _tree_response(["README.md", "src/app.py", "docs/guide.md"])
        )

        assert result.success is True
        assert result.data["has_tests"] is False

    @patch("agent.tools.github_tool.httpx")
    def test_tree_request_error_reports_false(
        self, mock_httpx: MagicMock, tool: GitHubTool
    ) -> None:
        """A failed tree request must degrade to False, not fail the analysis."""
        mock_httpx.get.side_effect = [
            _mock_response(REPO_JSON),
            httpx.RequestError("network unavailable"),
        ]
        head_response = MagicMock()
        head_response.status_code = 200
        mock_httpx.head.return_value = head_response

        result = tool.execute({"github_username": "octocat", "repo_name": "example-repo"})

        assert result.success is True
        assert result.data["has_tests"] is False

    @patch("agent.tools.github_tool.httpx")
    def test_missing_branch_reports_false(self, mock_httpx: MagicMock, tool: GitHubTool) -> None:
        """A non-200 tree response (e.g. unknown branch) degrades to False."""
        tree = _tree_response([])
        tree.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock()
        )

        result = self._execute(mock_httpx, tool, tree)

        assert result.success is True
        assert result.data["has_tests"] is False

    @patch("agent.tools.github_tool.httpx")
    def test_truncated_tree_still_reports_found_markers(
        self, mock_httpx: MagicMock, tool: GitHubTool
    ) -> None:
        """Truncation may under-report, but a marker already seen still counts."""
        result = self._execute(
            mock_httpx, tool, _tree_response(["tests/test_app.py"], truncated=True)
        )

        assert result.data["has_tests"] is True

    @patch("agent.tools.github_tool.httpx")
    def test_tree_fetched_recursively_from_default_branch(
        self, mock_httpx: MagicMock, tool: GitHubTool
    ) -> None:
        """Nested test files are only visible when the tree is fetched recursively."""
        repo_json = {**REPO_JSON, "default_branch": "develop"}
        mock_httpx.get.side_effect = [_mock_response(repo_json), _tree_response([])]
        head_response = MagicMock()
        head_response.status_code = 200
        mock_httpx.head.return_value = head_response

        tool.execute({"github_username": "octocat", "repo_name": "example-repo"})

        tree_call = mock_httpx.get.call_args_list[1]
        assert tree_call.args[0].endswith("/repos/octocat/example-repo/git/trees/develop")
        assert tree_call.kwargs["params"] == {"recursive": "1"}

    @patch("agent.tools.github_tool.httpx")
    def test_existing_metadata_fields_unchanged(
        self, mock_httpx: MagicMock, tool: GitHubTool
    ) -> None:
        """Adding has_tests must not disturb the other analysis fields."""
        result = self._execute(mock_httpx, tool, _tree_response(["tests/test_app.py"]))

        assert result.data["name"] == "example-repo"
        assert result.data["primary_language"] == "Python"
        assert result.data["star_count"] == 42
        assert result.data["fork_count"] == 7
        assert result.data["open_issues_count"] == 3
        assert result.data["last_commit_date"] == "2024-01-01T00:00:00Z"
        assert result.data["has_readme"] is True
        assert result.data["topics"] == ["python"]
        assert result.data["homepage"] == ""


@pytest.mark.unit
class TestPathIndicatesTests:
    """Path-level marker matching, including false-positive traps."""

    @pytest.mark.parametrize(
        "path",
        [
            "tests/test_app.py",
            "tests",
            "test/helpers.py",
            "backend/tests/unit/test_thing.py",
            "pytest.ini",
            "test_app.py",
            "src/test_utils.py",
            "TESTS/test_app.py",
        ],
    )
    def test_marker_paths_match(self, path: str) -> None:
        assert GitHubTool._path_indicates_tests(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "contest/entry.py",
            "latest/build.py",
            "src/protest.py",
            "docs/testing.md",
            "attestation.py",
            "src/app.py",
            "README.md",
            "",
        ],
    )
    def test_non_marker_paths_do_not_match(self, path: str) -> None:
        assert GitHubTool._path_indicates_tests(path) is False
