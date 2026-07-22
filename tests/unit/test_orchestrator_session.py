"""Reproduction test for issue #43.

Agent session state is not cleared between reviews for the same profile.

When a profile is reviewed a second time after changing (e.g. the user removed
their resume), the orchestrator loads the previous session and merges the new
results onto it via ``dict.update`` without ever clearing it. Results from tools
that no longer run in the new review therefore linger as stale state.

This test documents the current (buggy) behaviour with ``xfail(strict=True)``.
Once the fix lands in Week 9 it will pass, causing an ``XPASS`` that flags the
marker for removal.
"""

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult


class FakeRedis:
    """In-memory stand-in for redis.Redis so the test needs no Docker."""

    def __init__(self) -> None:
        self.store: dict = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, val) -> None:
        self.store[key] = val

    def delete(self, key) -> None:
        self.store.pop(key, None)


class FakeTool(BaseTool):
    """Minimal tool that reports which tool produced the result."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.description = name

    def execute(self, input_data: dict) -> ToolResult:
        return ToolResult(success=True, data={"tool": self.name})


@pytest.mark.unit
@pytest.mark.xfail(
    reason="Issue #43: session state is not cleared between reviews",
    strict=True,
)
def test_removed_tool_not_persisted_across_reviews() -> None:
    store = SessionStore(FakeRedis())
    tools = {name: FakeTool(name) for name in ("github_tool", "skill_extractor", "market_analyzer")}
    profile_id = "profile-1"

    # Review 1: profile has a resume, so skill_extractor runs and is stored.
    Orchestrator(tools, store).run(
        profile_id,
        {
            "github_username": "octocat",
            "projects": [{"github_repo": "hello"}],
            "resume_text": "Python dev",
        },
    )

    # Review 2: resume removed, so skill_extractor is NOT part of the plan.
    Orchestrator(tools, store).run(
        profile_id,
        {
            "github_username": "octocat",
            "projects": [{"github_repo": "hello"}],
        },
    )

    session = store.get(profile_id) or {}

    # The stale skill_extractor result from review 1 should not survive.
    assert "skill_extractor" not in session
