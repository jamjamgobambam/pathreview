"""Unit tests for GitHubTool, covering has_tests detection (issue #50).

These tests mock the ``httpx`` calls so they run offline and are not
subject to GitHub's rate limits.
"""

from unittest.mock import MagicMock, patch

import pytest

from agent.tools.github_tool import GitHubTool


def _contents_response(entries: object, status_code: int = 200) -> MagicMock:
    """Build a fake GitHub contents API response.

    Args:
        entries: Value returned by ``response.json()`` (normally a list
            of ``{"name": ..., "type": ...}`` entries).
        status_code: HTTP status code for the mocked response.

    Returns:
        A MagicMock standing in for an ``httpx.Response``.
    """
    resp = MagicMock(status_code=status_code)
    resp.json.return_value = entries
    return resp


@pytest.mark.unit
class TestGitHubToolHasTests:
    """Tests for GitHubTool._has_tests and the has_tests metadata field (#50)."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        """Create a GitHubTool instance."""
        return GitHubTool()

    def test_detects_tests_directory(self, tool: GitHubTool) -> None:
        """A root-level tests/ directory counts as having tests."""
        entries = [{"name": "tests", "type": "dir"}, {"name": "README.md", "type": "file"}]
        with patch("httpx.get", return_value=_contents_response(entries)):
            assert tool._has_tests("octocat", "hello-world") is True

    def test_detects_test_directory_singular(self, tool: GitHubTool) -> None:
        """A root-level test/ directory (singular) also counts."""
        entries = [{"name": "test", "type": "dir"}]
        with patch("httpx.get", return_value=_contents_response(entries)):
            assert tool._has_tests("octocat", "hello-world") is True

    def test_detects_pytest_ini(self, tool: GitHubTool) -> None:
        """A pytest.ini file counts as having tests."""
        entries = [{"name": "pytest.ini", "type": "file"}, {"name": "src", "type": "dir"}]
        with patch("httpx.get", return_value=_contents_response(entries)):
            assert tool._has_tests("octocat", "hello-world") is True

    def test_detects_root_test_file(self, tool: GitHubTool) -> None:
        """A root-level test_*.py file counts as having tests."""
        entries = [{"name": "test_main.py", "type": "file"}]
        with patch("httpx.get", return_value=_contents_response(entries)):
            assert tool._has_tests("octocat", "hello-world") is True

    def test_returns_false_when_no_test_indicators(self, tool: GitHubTool) -> None:
        """A repo with no test dir/file/config returns False."""
        entries = [
            {"name": "README.md", "type": "file"},
            {"name": "src", "type": "dir"},
            {"name": "main.py", "type": "file"},
        ]
        with patch("httpx.get", return_value=_contents_response(entries)):
            assert tool._has_tests("octocat", "hello-world") is False

    def test_does_not_match_non_test_python_file(self, tool: GitHubTool) -> None:
        """A file that merely contains 'test' in its name is not matched."""
        entries = [{"name": "latest.py", "type": "file"}, {"name": "contest.py", "type": "file"}]
        with patch("httpx.get", return_value=_contents_response(entries)):
            assert tool._has_tests("octocat", "hello-world") is False

    def test_returns_false_on_non_200_status(self, tool: GitHubTool) -> None:
        """A non-200 response (e.g. empty repo 404) returns False."""
        resp = _contents_response([], status_code=404)
        with patch("httpx.get", return_value=resp):
            assert tool._has_tests("octocat", "hello-world") is False

    def test_returns_false_when_contents_not_a_list(self, tool: GitHubTool) -> None:
        """The contents API returns a dict (not a list) on error payloads."""
        resp = _contents_response({"message": "Not Found"})
        with patch("httpx.get", return_value=resp):
            assert tool._has_tests("octocat", "hello-world") is False

    def test_returns_false_on_request_exception(self, tool: GitHubTool) -> None:
        """Network errors are handled gracefully and return False."""
        with patch("httpx.get", side_effect=Exception("boom")):
            assert tool._has_tests("octocat", "hello-world") is False

    def test_metadata_includes_has_tests_field(self, tool: GitHubTool) -> None:
        """execute() surfaces has_tests as a boolean in the metadata dict (#50)."""
        repo_json = {
            "name": "pathreview",
            "description": "AI-powered portfolio review assistant",
            "language": "Python",
            "stargazers_count": 0,
            "forks_count": 0,
            "open_issues_count": 0,
            "pushed_at": "2026-07-20T17:40:56Z",
            "topics": [],
            "homepage": "",
        }
        repo_resp = MagicMock(status_code=200)
        repo_resp.json.return_value = repo_json
        repo_resp.raise_for_status = MagicMock()

        contents_resp = _contents_response([{"name": "tests", "type": "dir"}])

        def get_dispatch(url: str, **kwargs: object) -> MagicMock:
            """Return the contents response for the contents URL, repo JSON otherwise."""
            if url.endswith("/contents"):
                return contents_resp
            return repo_resp

        with (
            patch("httpx.get", side_effect=get_dispatch),
            patch("httpx.head", return_value=MagicMock(status_code=200)),
        ):
            result = tool.execute({"github_username": "Alessandra005", "repo_name": "pathreview"})

        assert result.success is True
        assert "has_tests" in result.data
        assert result.data["has_tests"] is True
        assert isinstance(result.data["has_tests"], bool)
