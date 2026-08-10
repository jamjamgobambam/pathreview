"""Tests for github_tool.py"""

from typing import Any

import pytest

from agent.tools.github_tool import GitHubTool


class FakeResponse:
    """Simple fake httpx response."""

    def __init__(self, json_data: dict | None = None, status_code: int = 200) -> None:
        self._json_data = json_data or {}
        self.status_code = status_code

    def json(self) -> dict:
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            request = httpx.Request("GET", "https://api.github.com")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)


@pytest.mark.unit
class TestGitHubTool:
    """Test suite for GitHubTool."""

    @pytest.fixture
    def tool(self) -> GitHubTool:
        """Create a GitHubTool instance."""
        return GitHubTool(api_token="token")

    def test_fetch_repo_metadata_includes_file_tree(
        self, tool: GitHubTool, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test repo metadata includes the file tree from GitHub."""
        repo_response = FakeResponse(
            {
                "name": "demo",
                "description": "Demo repo",
                "language": "Python",
                "stargazers_count": 10,
                "forks_count": 2,
                "open_issues_count": 1,
                "pushed_at": "2026-07-31T00:00:00Z",
                "default_branch": "main",
                "topics": ["demo"],
                "homepage": "",
            }
        )
        branch_response = FakeResponse(
            {
                "commit": {
                    "commit": {
                        "tree": {
                            "sha": "tree-sha-123",
                        }
                    }
                }
            }
        )
        tree_response = FakeResponse(
            {
                "tree": [
                    {"path": "src/app.py", "type": "blob"},
                    {"path": "tests/test_app.py", "type": "blob"},
                    {"path": "src", "type": "tree"},
                ]
            }
        )
        head_response = FakeResponse(status_code=200)

        calls: list[str] = []

        def mock_get(
            url: str,
            headers: dict | None = None,
            timeout: float | None = None,
            params: dict | None = None,
        ) -> FakeResponse:
            calls.append(url)
            if url.endswith("/repos/demo-user/demo-repo"):
                return repo_response
            if url.endswith("/branches/main"):
                return branch_response
            if url.endswith("/git/trees/tree-sha-123"):
                return tree_response
            raise AssertionError(f"Unexpected GET url: {url}")

        def mock_head(
            url: str, headers: dict | None = None, timeout: float | None = None
        ) -> FakeResponse:
            calls.append(url)
            return head_response

        monkeypatch.setattr("agent.tools.github_tool.httpx.get", mock_get)
        monkeypatch.setattr("agent.tools.github_tool.httpx.head", mock_head)

        result = tool._fetch_repo_metadata("demo-user", "demo-repo")

        assert result["files"] == ["src/app.py", "tests/test_app.py"]
        assert result["has_readme"] is True
        assert "/branches/main" in "".join(calls)
        assert "/git/trees/tree-sha-123" in "".join(calls)

    def test_fetch_file_tree_gracefully_handles_failure(
        self, tool: GitHubTool, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test file tree failures degrade to an empty list."""

        def mock_get(*args: Any, **kwargs: Any) -> None:
            raise OSError("network down")

        monkeypatch.setattr("agent.tools.github_tool.httpx.get", mock_get)

        files = tool._fetch_file_tree("demo-user", "demo-repo", "main")

        assert files == []
