"""Reproduction / regression test for issue #43.

Agent session state is not cleared between reviews for the same user.
https://github.com/ascherj/pathreview/issues/43

Orchestrator.run() loads the previous session state and then does
`session_state.update(results)`, merging new results ONTO the old ones instead
of replacing them. So a tool that ran in an earlier review but not in a later
one leaves its stale output behind in the stored session.

This test currently FAILS (documents the bug). It should PASS once the
orchestrator clears prior state before persisting the current review.
"""

from typing import TYPE_CHECKING, cast

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult

if TYPE_CHECKING:
    import redis


class FakeRedis:
    """Minimal in-memory stand-in for the redis client SessionStore uses."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


class EchoTool(BaseTool):
    """Stub tool that echoes its input so we can tell which review produced it."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.description = name

    def execute(self, input_data: dict) -> ToolResult:
        return ToolResult(success=True, data={"tool": self.name, "input": input_data})


def _make_orchestrator(session_store: SessionStore) -> Orchestrator:
    tools = {
        "github_tool": EchoTool("github_tool"),
        "tech_detector": EchoTool("tech_detector"),
        "readme_scorer": EchoTool("readme_scorer"),
        "skill_extractor": EchoTool("skill_extractor"),
        "market_analyzer": EchoTool("market_analyzer"),
    }
    # A fresh Orchestrator per call models two independent review requests from
    # the same user, sharing one Redis-backed session store.
    return Orchestrator(tools=tools, session_store=session_store)


@pytest.mark.unit
def test_session_state_cleared_between_reviews() -> None:
    """A later review must not retain tool results from an earlier one."""
    # FakeRedis implements the subset of the redis client SessionStore uses.
    store = SessionStore(cast("redis.Redis", FakeRedis()))
    profile_id = "user-123"

    # Review 1: portfolio WITH a resume -> skill_extractor runs and is stored.
    profile_v1 = {
        "github_username": "janedoe",
        "projects": [{"github_repo": "weather-app"}],
        "readme_content": "# Weather App (v1)",
        "resume_text": "Python, FastAPI",
    }
    _make_orchestrator(store).run(profile_id, profile_v1)
    assert "skill_extractor" in (store.get(profile_id) or {})  # sanity: ran in review 1

    # Review 2: user updated the portfolio and REMOVED the resume, so
    # skill_extractor is not part of this review's plan.
    profile_v2 = {
        "github_username": "janedoe",
        "projects": [{"github_repo": "weather-app"}],
        "readme_content": "# Weather App (v2 - IMPROVED)",
    }
    _make_orchestrator(store).run(profile_id, profile_v2)

    stored = store.get(profile_id)
    assert stored is not None

    # The stored session should reflect ONLY review 2's tools. Today it still
    # contains review 1's skill_extractor -> this assertion fails (the bug).
    assert "skill_extractor" not in stored, (
        "Stale 'skill_extractor' from review 1 leaked into the session after "
        "review 2 (session state not cleared between reviews)."
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
