"""Tests for agent/tools/github_tool.py"""

from unittest.mock import Mock, patch

import pytest

from agent.tools.github_tool import GitHubTool


def _tree_response(paths: list[str]) -> Mock:
    """Build a mock httpx response mimicking the git-tree API."""
    response = Mock()
    response.raise_for_status = Mock()
    response.json = Mock(
        return_value={
            "tree": [{"path": p} for p in paths],
            "truncated": False,
        }
    )
    return response


@pytest.mark.unit
class TestDetectTests:
    """Test suite for GitHubTool._detect_tests."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        """Create a GitHubTool instance."""
        return GitHubTool()

    @pytest.mark.parametrize(
        "paths",
        [
            ["tests/test_foo.py"],  # tests/ directory
            ["src/main.py", "test/helper.py"],  # test/ directory
            ["pytest.ini", "src/app.py"],  # pytest config file
            ["test_main.py"],  # root-level test_*.py, no tests/ dir
            ["src/Tests/TEST_Foo.py"],  # case-insensitive match
        ],
    )
    def test_returns_true_when_tests_present(self, tool: GitHubTool, paths: list[str]) -> None:
        """has_tests is True when any path indicates tests."""
        with patch(
            "agent.tools.github_tool.httpx.get",
            return_value=_tree_response(paths),
        ):
            assert tool._detect_tests("octocat", "repo", "main") is True

    @pytest.mark.parametrize(
        "paths",
        [
            [],  # empty repo
            ["src/main.py", "README.md"],  # no tests at all
            ["contest/results.py", "latest/x.py"],  # substrings, not real test dirs
            ["src/mytest.py"],  # 'test' not a segment, no test_ prefix
        ],
    )
    def test_returns_false_when_no_tests(self, tool: GitHubTool, paths: list[str]) -> None:
        """has_tests is False when no path indicates tests (no false positives)."""
        with patch(
            "agent.tools.github_tool.httpx.get",
            return_value=_tree_response(paths),
        ):
            assert tool._detect_tests("octocat", "repo", "main") is False

    def test_returns_false_on_request_error(self, tool: GitHubTool) -> None:
        """Detection fails safe to False on any network error."""
        with patch(
            "agent.tools.github_tool.httpx.get",
            side_effect=Exception("boom"),
        ):
            assert tool._detect_tests("octocat", "repo", "main") is False

    def test_detects_with_api_token(self) -> None:
        """Detection still works (and sends auth header) when a token is set."""
        tool = GitHubTool(api_token="secret")
        captured: dict[str, object] = {}

        def get_side_effect(url: str, headers: dict | None = None, **kwargs: object) -> Mock:
            captured["headers"] = headers
            return _tree_response(["tests/test_foo.py"])

        with patch(
            "agent.tools.github_tool.httpx.get",
            side_effect=get_side_effect,
        ):
            assert tool._detect_tests("octocat", "repo", "main") is True
        assert captured["headers"]["Authorization"] == "token secret"  # type: ignore[index]


@pytest.mark.unit
class TestFetchRepoMetadata:
    """Test suite for GitHubTool metadata output, including has_tests."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        """Create a GitHubTool instance."""
        return GitHubTool()

    def test_execute_includes_has_tests(self, tool: GitHubTool) -> None:
        """execute() surfaces has_tests without dropping existing fields."""
        repo_response = Mock()
        repo_response.raise_for_status = Mock()
        repo_response.json = Mock(
            return_value={
                "name": "repo",
                "description": "desc",
                "language": "Python",
                "stargazers_count": 5,
                "forks_count": 1,
                "open_issues_count": 0,
                "pushed_at": "2024-01-01T00:00:00Z",
                "topics": [],
                "homepage": None,
                "default_branch": "develop",
            }
        )
        tree_response = _tree_response(["tests/test_app.py"])

        def get_side_effect(url: str, **kwargs: object) -> Mock:
            # The repo call and the tree call both go through httpx.get;
            # route by URL so default_branch ("develop") is exercised too.
            return tree_response if "/git/trees/" in url else repo_response

        with (
            patch(
                "agent.tools.github_tool.httpx.get",
                side_effect=get_side_effect,
            ),
            patch(
                "agent.tools.github_tool.httpx.head",
                return_value=Mock(status_code=200),
            ),
        ):
            result = tool.execute({"github_username": "octocat", "repo_name": "repo"})

        assert result.success is True
        assert result.data["has_tests"] is True
        # regression: existing fields still present and correct
        assert result.data["has_readme"] is True
        assert result.data["name"] == "repo"
        assert result.data["primary_language"] == "Python"
        assert result.data["star_count"] == 5

    def test_defaults_branch_to_main_when_absent(self, tool: GitHubTool) -> None:
        """When the API omits default_branch, the tree is fetched from 'main'."""
        repo_response = Mock()
        repo_response.raise_for_status = Mock()
        repo_response.json = Mock(return_value={"name": "repo"})  # no default_branch
        called_urls: list[str] = []

        def get_side_effect(url: str, **kwargs: object) -> Mock:
            called_urls.append(url)
            return _tree_response([]) if "/git/trees/" in url else repo_response

        with (
            patch(
                "agent.tools.github_tool.httpx.get",
                side_effect=get_side_effect,
            ),
            patch(
                "agent.tools.github_tool.httpx.head",
                return_value=Mock(status_code=200),
            ),
        ):
            result = tool.execute({"github_username": "octocat", "repo_name": "repo"})

        assert result.success is True
        assert result.data["has_tests"] is False
        assert any("/git/trees/main?recursive=1" in u for u in called_urls)
