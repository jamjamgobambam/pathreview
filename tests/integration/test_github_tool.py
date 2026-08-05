"""Integration tests for `GitHubTool` against a mock GitHub API server.

Covers issue #57. Every test runs offline against `pytest_httpserver` — no
network access, no GitHub credentials, no rate limits, and no assertions on
values that drift (star counts, push timestamps) because the payloads are
frozen fixtures rather than live responses.

See `conftest.py` for the mock server fixtures.
"""

import pytest
from pytest_httpserver import HTTPServer

from agent.tools.github_tool import GitHubTool

from .conftest import expect_readme, expect_repo, load_response


@pytest.mark.integration
class TestSuccessfulFetch:
    """Responses the tool is expected to parse into metadata."""

    def test_returns_full_metadata_for_a_well_formed_repo(
        self, httpserver: HTTPServer, github_tool: GitHubTool
    ) -> None:
        """The happy path: every metadata field is mapped from the response."""
        expect_repo(httpserver, "ascherj", "pathreview", load_response("repo_full"))
        expect_readme(httpserver, "ascherj", "pathreview")

        result = github_tool.execute({"github_username": "ascherj", "repo_name": "pathreview"})

        assert result.success is True
        assert result.error is None
        assert result.data == {
            "name": "pathreview",
            "description": "AI-powered portfolio review assistant",
            "primary_language": "Python",
            "star_count": 8,
            "fork_count": 3,
            "open_issues_count": 130,
            "last_commit_date": "2026-07-18T00:05:16Z",
            "has_readme": True,
            "topics": ["ai", "fastapi", "portfolio", "rag"],
            "homepage": "https://pathreview.dev",
        }

    def test_coerces_null_description_language_and_homepage(
        self, httpserver: HTTPServer, github_tool: GitHubTool
    ) -> None:
        """GitHub sends JSON `null` for unset fields; the tool substitutes defaults."""
        expect_repo(httpserver, "octocat", "scratch", load_response("repo_minimal_nulls"))
        expect_readme(httpserver, "octocat", "scratch")

        result = github_tool.execute({"github_username": "octocat", "repo_name": "scratch"})

        assert result.success is True
        assert result.data["description"] == ""
        assert result.data["primary_language"] == "Unknown"
        assert result.data["homepage"] == ""

    def test_defaults_topics_to_empty_list_when_key_is_absent(
        self, httpserver: HTTPServer, github_tool: GitHubTool
    ) -> None:
        """A response with no `topics` key must not raise a KeyError."""
        body = load_response("repo_minimal_nulls")
        assert "topics" not in body, "fixture must omit topics for this test to mean anything"
        expect_repo(httpserver, "octocat", "scratch", body)
        expect_readme(httpserver, "octocat", "scratch")

        result = github_tool.execute({"github_username": "octocat", "repo_name": "scratch"})

        assert result.success is True
        assert result.data["topics"] == []


@pytest.mark.integration
class TestErrorResponses:
    """HTTP failures the tool maps onto `ToolResult.error` messages."""

    def test_maps_404_to_repository_not_found(
        self, httpserver: HTTPServer, github_tool: GitHubTool
    ) -> None:
        """A missing repo becomes a friendly message, not a raised exception."""
        expect_repo(httpserver, "ascherj", "nonexistent", load_response("not_found"), status=404)

        result = github_tool.execute({"github_username": "ascherj", "repo_name": "nonexistent"})

        assert result.success is False
        assert result.data == {}
        assert result.error == "Repository not found"

    def test_maps_403_to_rate_limited_or_access_denied(
        self, httpserver: HTTPServer, github_tool: GitHubTool
    ) -> None:
        """The unauthenticated rate limit is the most likely real-world failure."""
        expect_repo(httpserver, "ascherj", "pathreview", load_response("rate_limited"), status=403)

        result = github_tool.execute({"github_username": "ascherj", "repo_name": "pathreview"})

        assert result.success is False
        assert result.data == {}
        assert result.error == "Rate limited or access denied"

    def test_reports_the_status_code_for_unmapped_errors(
        self, httpserver: HTTPServer, github_tool: GitHubTool
    ) -> None:
        """Anything other than 404/403 falls through to a generic message."""
        expect_repo(httpserver, "ascherj", "pathreview", {"message": "Server Error"}, status=500)

        result = github_tool.execute({"github_username": "ascherj", "repo_name": "pathreview"})

        assert result.success is False
        assert result.data == {}
        assert result.error == "GitHub API error: 500"

    def test_returns_error_without_making_a_request_when_input_is_missing(
        self, httpserver: HTTPServer, github_tool: GitHubTool
    ) -> None:
        """Input validation short-circuits before any HTTP call is attempted."""
        result = github_tool.execute({"github_username": "ascherj"})

        assert result.success is False
        assert result.error == "Missing github_username or repo_name"
        assert httpserver.log == [], "expected no HTTP request for invalid input"

    def test_returns_error_when_the_server_is_unreachable(self) -> None:
        """The CI failure mode before this change: no egress means no result.

        Port 9 (discard) has nothing listening. The error *message* is
        deliberately not asserted on — a refused connection surfaces as
        "WinError 10061" on Windows and "Connection refused" on Linux.
        """
        tool = GitHubTool(base_url="http://127.0.0.1:9")

        result = tool.execute({"github_username": "ascherj", "repo_name": "pathreview"})

        assert result.success is False
        assert result.data == {}
        assert result.error


@pytest.mark.integration
class TestReadmeDetection:
    """`_has_readme` fans a second, HEAD request out to a separate endpoint."""

    def test_reports_no_readme_when_the_endpoint_returns_404(
        self, httpserver: HTTPServer, github_tool: GitHubTool
    ) -> None:
        """A repo without a README still yields a successful result."""
        expect_repo(httpserver, "ascherj", "pathreview", load_response("repo_full"))
        expect_readme(httpserver, "ascherj", "pathreview", status=404)

        result = github_tool.execute({"github_username": "ascherj", "repo_name": "pathreview"})

        assert result.success is True
        assert result.data["has_readme"] is False

    def test_readme_failure_does_not_fail_the_whole_result(
        self, httpserver: HTTPServer, github_tool: GitHubTool
    ) -> None:
        """A broken README endpoint degrades one field, it does not raise."""
        expect_repo(httpserver, "ascherj", "pathreview", load_response("repo_full"))
        expect_readme(httpserver, "ascherj", "pathreview", status=500)

        result = github_tool.execute({"github_username": "ascherj", "repo_name": "pathreview"})

        assert result.success is True
        assert result.data["has_readme"] is False
        assert result.data["name"] == "pathreview"

    def test_one_execute_call_hits_both_endpoints(
        self, httpserver: HTTPServer, github_tool: GitHubTool
    ) -> None:
        """Pins the two-request fan-out any future mock or cache has to honour."""
        expect_repo(httpserver, "ascherj", "pathreview", load_response("repo_full"))
        expect_readme(httpserver, "ascherj", "pathreview")

        github_tool.execute({"github_username": "ascherj", "repo_name": "pathreview"})

        assert [(req.method, req.path) for req, _ in httpserver.log] == [
            ("GET", "/repos/ascherj/pathreview"),
            ("HEAD", "/repos/ascherj/pathreview/readme"),
        ]


@pytest.mark.integration
class TestAuthentication:
    """Token propagation, asserted on the requests the server actually received."""

    def test_sends_the_token_on_both_requests(
        self, httpserver: HTTPServer, mock_github_url: str
    ) -> None:
        """The README HEAD needs the token too, or it 404s on private repos."""
        expect_repo(httpserver, "ascherj", "pathreview", load_response("repo_full"))
        expect_readme(httpserver, "ascherj", "pathreview")
        tool = GitHubTool(api_token="ghp_testtoken", base_url=mock_github_url)

        tool.execute({"github_username": "ascherj", "repo_name": "pathreview"})

        sent = [req.headers.get("Authorization") for req, _ in httpserver.log]
        assert sent == ["token ghp_testtoken", "token ghp_testtoken"]

    def test_sends_no_authorization_header_when_no_token_is_given(
        self, httpserver: HTTPServer, github_tool: GitHubTool
    ) -> None:
        """Unauthenticated requests must not send an empty or malformed header."""
        expect_repo(httpserver, "ascherj", "pathreview", load_response("repo_full"))
        expect_readme(httpserver, "ascherj", "pathreview")

        github_tool.execute({"github_username": "ascherj", "repo_name": "pathreview"})

        assert [req.headers.get("Authorization") for req, _ in httpserver.log] == [None, None]


@pytest.mark.integration
class TestBaseUrlInjection:
    """The seam that makes all of the above possible (issue #57)."""

    def test_defaults_to_the_public_github_api(self) -> None:
        """Production behaviour is unchanged when no base URL is supplied."""
        assert GitHubTool().base_url == "https://api.github.com"

    def test_accepts_an_override_without_a_token(self) -> None:
        """`base_url` is keyword-usable on its own, not just alongside a token."""
        assert GitHubTool(base_url="http://localhost:1234").base_url == "http://localhost:1234"

    def test_first_positional_argument_is_still_the_token(self) -> None:
        """Backwards compatibility for existing positional call sites."""
        tool = GitHubTool("ghp_positional")

        assert tool.api_token == "ghp_positional"
        assert tool.base_url == "https://api.github.com"
