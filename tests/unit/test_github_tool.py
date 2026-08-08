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
        """A repo with a tests/ dir in its root listing should surface has_tests=True."""

        contents_json = [{"name": "tests", "type": "dir"}, {"name": "README.md", "type": "file"}]

        def fake_get(
            url: str, headers: dict | None = None, timeout: float | None = None
        ) -> _FakeResponse:
            if url.endswith("/contents"):
                return _FakeResponse(200, contents_json)  # type: ignore[arg-type]
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
        assert result.data["has_tests"] is True

    def test_has_tests_false_when_no_test_indicators(
        self, monkeypatch: pytest.MonkeyPatch, repo_json: dict
    ) -> None:
        """A repo with no test dir/file indicators in its root listing → has_tests=False."""

        contents_json = [{"name": "README.md", "type": "file"}, {"name": "src", "type": "dir"}]

        def fake_get(
            url: str, headers: dict | None = None, timeout: float | None = None
        ) -> _FakeResponse:
            if url.endswith("/contents"):
                return _FakeResponse(200, contents_json)  # type: ignore[arg-type]
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
        assert result.data["has_tests"] is False

    def test_has_tests_false_when_contents_request_fails(
        self, monkeypatch: pytest.MonkeyPatch, repo_json: dict
    ) -> None:
        """A failed contents lookup (e.g. 404/rate-limit) shouldn't break the whole fetch."""

        def fake_get(
            url: str, headers: dict | None = None, timeout: float | None = None
        ) -> _FakeResponse:
            if url.endswith("/contents"):
                return _FakeResponse(404, {})
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
        assert result.data["has_tests"] is False
