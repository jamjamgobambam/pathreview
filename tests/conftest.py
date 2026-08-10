"""
Pytest fixtures for GitHub integration tests, backed by pytest-httpserver.

pytest-httpserver (a pytest plugin) runs a real local HTTP server and
gives us the `httpserver` fixture automatically. We register one
catch-all handler on it per HTTP method; the handler resolves fixture
files by request path (see fixture_resolver.py) instead of us having
to declare every route by hand.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from werkzeug.wrappers import Request, Response

from .fixture_resolver import not_found_body, resolve_fixture

if TYPE_CHECKING:
    # NOTE: adjust this import to match where GitHubTool actually lives
    # in your package. This branch only runs for static type checking,
    # never at runtime, so it's safe even before you fix the path.
    from collections.abc import Callable

    from pytest_httpserver import HTTPServer

    from agent.tools.github_tool import GitHubTool


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "github_responses"

# Matches any path — routing is done by looking the path up on disk,
# not by declaring individual routes.
ANY_PATH = re.compile(r".*")

HTTP_METHODS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]


def _make_handler(fixtures_dir: Path) -> Callable[[Request], Response]:
    def handler(request: Request) -> Response:
        is_head = request.method == "HEAD"
        lookup_method = "GET" if is_head else request.method

        result = resolve_fixture(fixtures_dir, request.path, lookup_method)

        status: int
        headers: dict[str, str]
        body: Any

        if result is None:
            status, headers, body = 404, {}, not_found_body(request.path)
        else:
            status, headers, body = result

        if is_head:
            # HEAD responses carry no body, only status/headers.
            return Response(status=status, headers=headers)
        return Response(
            json.dumps(body), status=status, headers=headers, content_type="application/json"
        )

    return handler


@pytest.fixture
def github_mock_server(httpserver: HTTPServer) -> str:
    """Registers the fixture-driven catch-all handler on pytest-httpserver.

    Returns the server's base URL, e.g. "http://localhost:54321".
    """
    handler = _make_handler(FIXTURES_DIR)
    for method in HTTP_METHODS:
        httpserver.expect_request(ANY_PATH, method=method).respond_with_handler(handler)

    base_url: str = httpserver.url_for("/")
    return base_url.rstrip("/")


@pytest.fixture
def github_tool(github_mock_server: str) -> GitHubTool:
    """A GitHubTool instance pointed at the mock server instead of the real API."""
    # NOTE: adjust this import to match where GitHubTool actually lives
    # in your package — keep it in sync with the TYPE_CHECKING import above.
    from agent.tools.github_tool import GitHubTool

    tool = GitHubTool(api_token="fake-token-for-tests")
    tool.base_url = github_mock_server
    return tool


"""Shared test fixtures for PathReview."""


@pytest.fixture
def sample_resume_text() -> str:
    """Return a sample resume text for testing."""
    return """
    Jane Doe
    Software Engineer
    jane.doe@example.com | github.com/janedoe

    Experience:
    - Software Engineer at TechCorp (2022-2024)
      Built REST APIs using Python and FastAPI.

    Education:
    - B.S. Computer Science, State University (2022)

    Skills: Python, JavaScript, React, PostgreSQL, Docker
    """


@pytest.fixture
def sample_readme_text() -> str:
    """Return a sample README text for testing."""
    return """
    # Weather App
    A weather forecasting application built with React and OpenWeatherMap API.

    ## Features
    - Current weather display
    - 5-day forecast
    - Location search

    ## Tech Stack
    - React 18
    - TypeScript
    - Tailwind CSS
    - OpenWeatherMap API
    """
