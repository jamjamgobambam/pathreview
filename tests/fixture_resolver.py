"""
Fixture resolution logic for the mock GitHub server.

This module is deliberately framework-agnostic: given a fixtures
directory, a request path, and an HTTP method, it figures out which
fixture file (if any) answers the request and what status/headers/body
it should produce. `conftest.py` wires this up to a real HTTP server
via pytest-httpserver.

Fixture resolution for e.g. GET /repos/octocat/hello-world:
    <fixtures_dir>/repos/octocat/hello-world.GET.json   (method-specific)
    <fixtures_dir>/repos/octocat/hello-world.json       (fallback)

A fixture file is either:
  * a plain JSON body -> served with status 200, or
  * an "envelope" with an explicit status:
        {
          "__status": 404,
          "__body": { "message": "Not Found", ... }
        }
"""

import json
from pathlib import Path
from typing import Any, TypeAlias

FixtureResponse: TypeAlias = tuple[int, dict[str, str], Any]


def candidate_paths(fixtures_dir: Path, req_path: str, method: str) -> list[Path]:
    base = req_path.strip("/")
    return [
        fixtures_dir / f"{base}.{method}.json",
        fixtures_dir / f"{base}.json",
    ]


def resolve_fixture(fixtures_dir: Path, req_path: str, method: str) -> FixtureResponse | None:
    """Returns (status, headers, body) for the first matching fixture, or None."""
    for candidate in candidate_paths(fixtures_dir, req_path, method):
        if candidate.is_file():
            return _load(candidate)
    return None


def _load(fixture_path: Path) -> FixtureResponse:
    data = json.loads(fixture_path.read_text())

    if isinstance(data, dict) and "__body" in data:
        status = data.get("__status", 200)
        headers = data.get("__headers", {})
        body = data["__body"]
    else:
        status, headers, body = 200, {}, data

    return status, headers, body


def not_found_body(req_path: str) -> dict:
    return {
        "message": "Not Found",
        "documentation_url": "https://docs.github.com/rest",
        "_mock_note": f"No fixture found for '/{req_path}'. Add one under the fixtures directory.",
    }
