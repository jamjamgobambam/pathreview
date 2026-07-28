"""Reproduction test for issue #43: session state not cleared between reviews.

Orchestrator.run() keys the session store by profile_id (per-user) instead of a
per-session/per-review id, and merges old session_state into new results via
session_state.update(results). This test proves that a second review for the
same profile can be served a stale tool result left over from a prior review,
even though the tool would produce different output for the new input.
"""

from typing import Any

import pytest

from agent.orchestrator import Orchestrator


class FakeSessionStore:
    """In-memory stand-in for the Redis-backed SessionStore."""

    def __init__(self) -> None:
        self._data: dict[str, dict] = {}

    def get(self, session_id: str) -> dict | None:
        return self._data.get(session_id)

    def set(self, session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
        self._data[session_id] = data

    def delete(self, session_id: str) -> None:
        self._data.pop(session_id, None)


class FakeGithubTool:
    """Returns whatever repo_name it was called with, so we can tell fresh
    results apart from stale ones."""

    name = "github_tool"

    def execute(self, tool_input: dict) -> Any:
        class Result:
            success = True
            data = {"repo_name": tool_input["repo_name"]}

        return Result()


class FakeTechDetector:
    """Returns whatever files it was called with."""

    name = "tech_detector"

    def execute(self, tool_input: dict) -> Any:
        class Result:
            success = True
            data = {"files": tool_input["files"]}

        return Result()


@pytest.mark.unit
class TestOrchestratorSessionState:
    def test_stale_tool_result_carried_into_review_where_tool_did_not_run(self) -> None:
        tools = {
            "github_tool": FakeGithubTool(),
            "tech_detector": FakeTechDetector(),
        }
        session_store = FakeSessionStore()

        profile_id = "user-123"

        # First review: profile has both a repo and a file listing, so both
        # tools execute and their results are persisted under profile_id.
        first_profile = {
            "github_username": "octocat",
            "projects": [{"github_repo": "repo-old"}],
            "files": ["main.py"],
        }
        orchestrator = Orchestrator(tools=tools, session_store=session_store)  # type: ignore[arg-type]
        first_result = orchestrator.run(profile_id, first_profile)
        assert first_result["tool_results"]["tech_detector"]["files"] == ["main.py"]

        # Second review for the SAME profile_id: the user removed their file
        # listing (e.g. reverted to a repo-only profile), so tech_detector
        # should not run and should not appear as a current result.
        second_profile = {
            "github_username": "octocat",
            "projects": [{"github_repo": "repo-new"}],
        }
        orchestrator_second_request = Orchestrator(tools=tools, session_store=session_store)  # type: ignore[arg-type]
        orchestrator_second_request.run(profile_id, second_profile)

        # Expected: the persisted session blob for this profile should only
        # reflect the current review, so tech_detector (not part of this
        # run's plan) should not be present.
        # Actual (bug): Orchestrator.run() loads session_state by profile_id
        # (not a per-review/session id) and does
        # `session_state.update(results)` before persisting it back. Since
        # session_state starts as whatever was stored last time, keys the new
        # plan didn't touch (like tech_detector here) are never cleared and
        # get re-persisted under the same profile_id, bleeding stale state
        # from the first review into the second.
        persisted_state = session_store.get(profile_id)
        assert persisted_state is not None
        assert "tech_detector" not in persisted_state
