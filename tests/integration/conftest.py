"""Fixtures for the mock GitHub API server used by integration tests.

`pytest_httpserver` starts a real HTTP server on an ephemeral localhost port,
so these tests exercise the genuine `httpx` request path — headers, status
codes, timeouts and all — without touching the network or needing credentials.

Response bodies are recorded GitHub payloads stored under
`tests/fixtures/github_responses/`, trimmed to the fields the tool reads.
"""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from pytest_httpserver import HTTPServer

from agent.tools.github_tool import GitHubTool

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "github_responses"


def load_response(name: str) -> dict[str, Any]:
    """Load a recorded GitHub API response body.

    Args:
        name: Fixture file name without the `.json` suffix

    Returns:
        The parsed JSON body

    Raises:
        FileNotFoundError: If no such fixture exists
    """
    path = FIXTURE_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No GitHub response fixture named {name!r} in {FIXTURE_DIR}")

    parsed: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return parsed


def expect_repo(
    httpserver: HTTPServer,
    username: str,
    repo_name: str,
    body: dict[str, Any] | None = None,
    status: int = 200,
) -> None:
    """Register the `GET /repos/{username}/{repo_name}` endpoint on the mock.

    Args:
        httpserver: The running mock server
        username: GitHub username in the request path
        repo_name: Repository name in the request path
        body: JSON body to return, defaults to an empty object
        status: HTTP status code to return
    """
    httpserver.expect_request(f"/repos/{username}/{repo_name}", method="GET").respond_with_json(
        body if body is not None else {}, status=status
    )


def expect_readme(
    httpserver: HTTPServer,
    username: str,
    repo_name: str,
    status: int = 200,
) -> None:
    """Register the `HEAD /repos/{username}/{repo_name}/readme` endpoint on the mock.

    A single `execute()` call fans out to two requests, because `_has_readme`
    is invoked while building the metadata dict. The second one is a HEAD, and
    a HEAD response carries no body.

    Args:
        httpserver: The running mock server
        username: GitHub username in the request path
        repo_name: Repository name in the request path
        status: HTTP status code to return
    """
    httpserver.expect_request(
        f"/repos/{username}/{repo_name}/readme", method="HEAD"
    ).respond_with_data("", status=status)


@pytest.fixture(scope="session")
def httpserver_listen_address() -> tuple[str, int]:
    """Bind the mock server to the IPv4 loopback address on an ephemeral port.

    Overrides `pytest_httpserver`'s default of `localhost`, which is worth the
    two lines: on a dual-stack host `localhost` resolves to `::1` before
    `127.0.0.1`, and since the server listens on IPv4 only, every request first
    burns ~2.6s on the dead IPv6 address before falling back. Binding to the
    literal IP takes the suite from ~60s to a few seconds.
    """
    return ("127.0.0.1", 0)


@pytest.fixture
def mock_github_url(httpserver: HTTPServer) -> str:
    """Return the mock server's base URL with no trailing slash.

    `url_for("")` yields `http://127.0.0.1:<port>/`, and the tool builds URLs
    by concatenation (`f"{base_url}/repos/..."`), so the slash has to go or
    every path arrives as `//repos/...` and matches no handler.
    """
    # Annotated rather than returned directly: the pre-commit mypy hook runs in
    # an isolated env without pytest-httpserver, where url_for() is untyped and
    # would otherwise trip warn_return_any.
    root: str = httpserver.url_for("")
    return root.rstrip("/")


@pytest.fixture
def github_tool(httpserver: HTTPServer, mock_github_url: str) -> Iterator[GitHubTool]:
    """Return an unauthenticated `GitHubTool` pointed at the mock server.

    On teardown it asserts every request the tool made was matched by a
    registered handler. That check matters here: `_has_readme` swallows all
    exceptions and returns `False`, so a mock that never matched would
    otherwise surface as a quietly passing test rather than an error.
    """
    yield GitHubTool(base_url=mock_github_url)
    httpserver.check_assertions()
