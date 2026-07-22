"""Tests for github_tool.py — reproduction for issue #50 (has_tests missing)."""

import httpx
import pytest

from agent.tools.github_tool import GitHubTool


class _FakeResponse:
    def __init__(self, status_code: int = 200, json_data: dict | None = None) -> None:
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self) -> dict:
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)  # type: ignore[arg-type]


@pytest.mark.unit
class TestGitHubToolHasTests:
    """Reproduces issue #50: `has_tests` is never included in tool output."""

    @pytest.fixture
    def repo_json(self) -> dict:
        return {
            "name": "pathreview",
            "description": "A repo with real tests",
            "language": "Python",
            "stargazers_count": 7,
            "forks_count": 2,
            "open_issues_count": 1,
            "pushed_at": "2026-07-18T00:05:16Z",
            "topics": [],
            "homepage": "",
        }

    def test_execute_includes_has_tests_field(
        self, monkeypatch: pytest.MonkeyPatch, repo_json: dict
    ) -> None:
        """A repo known to contain tests/ should surface has_tests=True.

        Currently fails: `_fetch_repo_metadata` never computes or includes
        `has_tests` in its output, regardless of whether the target repo
        actually has tests.
        """

        def fake_get(
            url: str, headers: dict | None = None, timeout: float | None = None
        ) -> _FakeResponse:
            return _FakeResponse(200, repo_json)

        def fake_head(
            url: str, headers: dict | None = None, timeout: float | None = None
        ) -> _FakeResponse:
            return _FakeResponse(200)

        monkeypatch.setattr("agent.tools.github_tool.httpx.get", fake_get)
        monkeypatch.setattr("agent.tools.github_tool.httpx.head", fake_head)

        tool = GitHubTool()
        result = tool.execute({"github_username": "ascherj", "repo_name": "pathreview"})

        assert result.success is True
        assert "has_tests" in result.data, "has_tests is missing from GitHubTool output — issue #50"
