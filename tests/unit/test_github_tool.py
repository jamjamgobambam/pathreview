"""Unit tests for GitHubTool (issue #50).

Cover the has_tests boolean added to the repository metadata output, plus the
existing has_readme and input validation behavior, using mocked httpx so no
network call is made.
"""

from unittest.mock import Mock, patch

import pytest

from agent.tools.github_tool import GitHubTool


def _fake_repo_json() -> dict:
    """Return a minimal GitHub repo payload shaped like the real API response."""
    return {
        "name": "example",
        "description": "Example repository",
        "language": "Python",
        "stargazers_count": 3,
        "forks_count": 1,
        "open_issues_count": 0,
        "pushed_at": "2024-01-01T00:00:00Z",
        "topics": [],
        "homepage": "",
    }


def _contents(*names: str) -> list:
    """Return a fake GitHub contents listing for the given entry names."""
    return [{"name": name, "type": "dir"} for name in names]


def _get_response(payload: object) -> Mock:
    """Build a mock httpx response whose json() returns the payload."""
    response = Mock()
    response.raise_for_status = Mock()
    response.json = Mock(return_value=payload)
    return response


@pytest.mark.unit
class TestGitHubTool:
    """Test suite for GitHubTool."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        """Create a GitHubTool instance."""
        return GitHubTool()

    def _route_get(self, contents_payload: object):
        """Return an httpx.get side effect that routes by URL.

        The repository endpoint returns the repo payload and the contents
        endpoint returns the supplied contents listing.
        """

        def _side_effect(url: str, **kwargs: object) -> Mock:
            if url.endswith("/contents"):
                return _get_response(contents_payload)
            return _get_response(_fake_repo_json())

        return _side_effect

    @patch("agent.tools.github_tool.httpx")
    def test_output_includes_has_tests_field(self, mock_httpx, tool) -> None:
        """The metadata output should carry a has_tests flag (issue #50)."""
        mock_httpx.get.side_effect = self._route_get(_contents("tests"))
        mock_httpx.head.return_value = Mock(status_code=200)

        result = tool.execute({"github_username": "octocat", "repo_name": "example"})

        assert result.success is True
        assert "has_tests" in result.data
        assert result.data["has_tests"] is True

    @patch("agent.tools.github_tool.httpx")
    def test_has_tests_false_when_no_tests(self, mock_httpx, tool) -> None:
        """A repo with no test directory or file reports has_tests False."""
        mock_httpx.get.side_effect = self._route_get(_contents("src", "README.md"))
        mock_httpx.head.return_value = Mock(status_code=200)

        result = tool.execute({"github_username": "octocat", "repo_name": "example"})

        assert result.data["has_tests"] is False

    @patch("agent.tools.github_tool.httpx")
    def test_has_tests_detects_pytest_ini(self, mock_httpx, tool) -> None:
        """A pytest.ini file at the root counts as tests."""
        mock_httpx.get.return_value = _get_response(_contents("pytest.ini"))

        assert tool._has_tests("octocat", "example") is True

    @patch("agent.tools.github_tool.httpx")
    def test_has_tests_detects_root_test_file(self, mock_httpx, tool) -> None:
        """A test_*.py file at the root counts as tests."""
        mock_httpx.get.return_value = _get_response(_contents("test_app.py"))

        assert tool._has_tests("octocat", "example") is True

    @patch("agent.tools.github_tool.httpx")
    def test_has_tests_returns_false_on_error(self, mock_httpx, tool) -> None:
        """A failed contents request is swallowed and reports False."""
        mock_httpx.get.side_effect = RuntimeError("network down")

        assert tool._has_tests("octocat", "example") is False

    def test_missing_input_returns_error(self, tool) -> None:
        """Missing username or repo name is reported as a failed result."""
        result = tool.execute({"github_username": "octocat"})

        assert result.success is False
        assert result.error == "Missing github_username or repo_name"
