"""Tests for orchestrator.py

Regression coverage for issue #43: agent session state is not cleared between
reviews for the same user. The orchestrator must treat each review as a fresh
analysis, so stale tool results from a previous review (e.g. github_tool for a
project the user has since removed) must not linger in the stored session.
"""

import json

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult


class FakeRedis:
    """Minimal in-memory stand-in for redis.Redis used by SessionStore."""

    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


class EchoTool(BaseTool):
    """Tool stub that echoes its input and counts how often it runs."""

    def __init__(self, name):
        self.name = name
        self.description = name
        self.calls = 0

    def execute(self, input_data: dict) -> ToolResult:
        self.calls += 1
        return ToolResult(success=True, data={"tool": self.name, "input": input_data})


@pytest.mark.unit
class TestOrchestratorSessionState:
    """Regression tests for cross-review session-state leakage (issue #43)."""

    PROFILE_ID = "user-123"

    @pytest.fixture
    def tools(self):
        """Tool set covering the plan branches used in these scenarios."""
        return {
            "github_tool": EchoTool("github_tool"),
            "readme_scorer": EchoTool("readme_scorer"),
            "market_analyzer": EchoTool("market_analyzer"),
        }

    @pytest.fixture
    def store(self):
        """Redis-backed session store using an in-memory fake."""
        return SessionStore(FakeRedis())

    def _stored_state(self, store):
        """Return the persisted session dict for PROFILE_ID (or None)."""
        raw = store.redis.store.get(f"session:{self.PROFILE_ID}")
        return json.loads(raw) if raw is not None else None

    def test_first_review_persists_only_current_plan(self, tools, store):
        """A first review (no prior state) stores exactly its own tool results."""
        orch = Orchestrator(tools, session_store=store)

        profile = {
            "github_username": "janedoe",
            "projects": [{"github_repo": "weather-app"}],
            "readme_content": "# Weather App v1",
        }
        result = orch.run(self.PROFILE_ID, profile)

        expected = {"github_tool", "readme_scorer", "market_analyzer"}
        assert set(result["tool_results"].keys()) == expected
        assert set(self._stored_state(store).keys()) == expected

    def test_removed_project_leaves_no_stale_state(self, tools, store):
        """After a project is removed, the prior github_tool result must not persist.

        This is the core reproduction of issue #43: review 1 runs github_tool,
        review 2 (same user, project removed) does not, and the stored session
        after review 2 must reflect only review 2's plan.
        """
        # Review 1: user has a GitHub repo + README.
        orch1 = Orchestrator(tools, session_store=store)
        orch1.run(
            self.PROFILE_ID,
            {
                "github_username": "janedoe",
                "projects": [{"github_repo": "weather-app"}],
                "readme_content": "# Weather App v1",
            },
        )
        assert "github_tool" in self._stored_state(store)

        # Review 2: project removed; a fresh Orchestrator (new process/request)
        # shares the same Redis-backed store, as in production.
        orch2 = Orchestrator(tools, session_store=store)
        result = orch2.run(
            self.PROFILE_ID,
            {"readme_content": "# Weather App v2 (repo removed)"},
        )

        stored = self._stored_state(store)
        # The stale result from review 1 must be gone.
        assert "github_tool" not in stored
        # Stored state reflects only review 2's plan.
        expected = {"readme_scorer", "market_analyzer"}
        assert set(stored.keys()) == expected
        assert set(result["tool_results"].keys()) == expected

    def test_second_review_reflects_updated_content(self, tools, store):
        """A re-run for the same user reflects the new input, not the old one."""
        orch1 = Orchestrator(tools, session_store=store)
        orch1.run(self.PROFILE_ID, {"readme_content": "# v1"})

        orch2 = Orchestrator(tools, session_store=store)
        orch2.run(self.PROFILE_ID, {"readme_content": "# v2"})

        stored = self._stored_state(store)
        assert stored["readme_scorer"]["input"]["readme_content"] == "# v2"

    def test_runs_without_session_store(self, tools):
        """Orchestrator works when no session store is configured."""
        orch = Orchestrator(tools, session_store=None)

        result = orch.run(self.PROFILE_ID, {"readme_content": "# No persistence"})

        assert "readme_scorer" in result["tool_results"]
