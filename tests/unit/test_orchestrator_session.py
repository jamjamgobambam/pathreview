"""Regression tests for issue #43.

Agent session state must not carry over between reviews of the same profile.

``Orchestrator.run()`` used to load the previous session and merge the new
results onto it via ``dict.update``, so results from tools that no longer ran in
a later review lingered as stale state. The fix persists only the current run's
results, so each review reflects exactly the tools that ran this time. These
tests guard that behaviour.
"""

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult


class FakeRedis:
    """In-memory stand-in for redis.Redis so the tests need no Docker."""

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


class EchoTool(BaseTool):
    """Tool whose output depends on its input, to detect stale/overwritten data."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.description = name

    def execute(self, input_data: dict) -> ToolResult:
        return ToolResult(success=True, data={"repo": input_data.get("repo_name")})


@pytest.mark.unit
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


@pytest.mark.unit
def test_tool_run_in_both_reviews_is_overwritten() -> None:
    store = SessionStore(FakeRedis())
    tools = {"github_tool": EchoTool("github_tool"), "market_analyzer": FakeTool("market_analyzer")}
    profile_id = "profile-2"

    # Review 1 analyses the "hello" repo.
    Orchestrator(tools, store).run(
        profile_id,
        {"github_username": "octocat", "projects": [{"github_repo": "hello"}]},
    )

    # Review 2 analyses a different repo for the same profile.
    Orchestrator(tools, store).run(
        profile_id,
        {"github_username": "octocat", "projects": [{"github_repo": "world"}]},
    )

    session = store.get(profile_id) or {}

    # The result should reflect the current review, not the stale one.
    assert session["github_tool"] == {"repo": "world"}


@pytest.mark.unit
def test_empty_second_review_clears_session() -> None:
    store = SessionStore(FakeRedis())
    tools = {name: FakeTool(name) for name in ("github_tool", "market_analyzer")}
    profile_id = "profile-3"

    # Review 1 runs tools and populates the session.
    Orchestrator(tools, store).run(
        profile_id,
        {"github_username": "octocat", "projects": [{"github_repo": "hello"}]},
    )
    assert store.get(profile_id)  # sanity: session is populated

    # Review 2 has no analysable data, so the plan is empty.
    Orchestrator(tools, store).run(profile_id, {})

    session = store.get(profile_id) or {}

    # No tools ran this time, so no stale results should remain.
    assert session == {}
