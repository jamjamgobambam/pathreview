"""Reproduction tests for issue #43.

Agent session state is not cleared between reviews for the same user.

The orchestrator persists per-profile tool results in a Redis-backed session
store keyed only by profile ID (`agent/memory/session_store.py`), and memoizes
tool results in an instance-level `ContextManager`
(`agent/memory/context_manager.py`). Neither cache is invalidated when a new
review starts (`Orchestrator.run` in `agent/orchestrator.py`).

As a result, a second review for the same profile replays cached tool outputs
from the earlier run instead of re-analyzing the freshly updated portfolio.

These tests document the reproduced issue and are expected to FAIL until the
session/context state is cleared (or namespaced) at the start of each review.
"""

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult


class _FakeRedis:
    """Minimal in-memory stand-in for the Redis client used by SessionStore."""

    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


class _CountingTool(BaseTool):
    """Tool whose output changes every time it is executed.

    Simulates a tool (e.g. the GitHub tool) that fetches live portfolio data:
    the *input* stays the same across reviews, but the *result* should reflect
    the latest portfolio state on each run.
    """

    name = "github_tool"
    description = "Counts executions to detect stale cached results."

    def __init__(self):
        self.calls = 0

    def execute(self, input_data: dict) -> ToolResult:
        self.calls += 1
        return ToolResult(success=True, data={"call": self.calls})


@pytest.mark.unit
class TestOrchestratorSessionStateBetweenReviews:
    """Reproduces issue #43: stale session state leaks across reviews."""

    def _make_orchestrator(self):
        tool = _CountingTool()
        store = SessionStore(_FakeRedis())
        orchestrator = Orchestrator({"github_tool": tool}, session_store=store)
        return orchestrator, tool, store

    def test_second_review_reexecutes_tools_after_portfolio_change(self):
        """A repeat review for the same profile should re-run the tools.

        Currently FAILS: the second review returns the first review's memoized
        result ({"call": 1}) instead of a fresh analysis ({"call": 2}).
        """
        orchestrator, _tool, _store = self._make_orchestrator()
        profile_data = {
            "github_username": "octocat",
            "projects": [{"github_repo": "repo1"}],
        }

        first = orchestrator.run("profile-1", profile_data)
        assert first["tool_results"]["github_tool"] == {"call": 1}

        # Same user starts a new review after updating their portfolio upstream.
        second = orchestrator.run("profile-1", profile_data)
        assert second["tool_results"]["github_tool"] == {"call": 2}

    def test_new_review_does_not_inherit_previous_session_state(self):
        """Persisted session state must not carry over into a new review.

        Currently FAILS: after a second review whose plan produces no tools,
        the persisted session still contains the stale "github_tool" result
        from the first review, proving the state is never invalidated.
        """
        orchestrator, _tool, store = self._make_orchestrator()

        orchestrator.run(
            "profile-1",
            {"github_username": "octocat", "projects": [{"github_repo": "repo1"}]},
        )
        assert "github_tool" in (store.get("profile-1") or {})

        # New review for the same profile with no analyzable data.
        orchestrator.run("profile-1", {})

        persisted = store.get("profile-1") or {}
        assert "github_tool" not in persisted
