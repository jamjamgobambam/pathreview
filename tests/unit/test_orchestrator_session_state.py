"""Regression tests for issue #43 — clear agent state between reviews."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import Mock

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator


class FakeSessionStore:
    """In-memory stand-in for SessionStore (no Redis required)."""

    def __init__(self) -> None:
        self._data: dict[str, dict] = {}

    def get(self, session_id: str) -> dict | None:
        data = self._data.get(session_id)
        return dict(data) if data is not None else None

    def set(self, session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
        self._data[session_id] = dict(data)

    def delete(self, session_id: str) -> None:
        self._data.pop(session_id, None)


class CountingTool:
    """Tool that returns a different payload on every execute() call."""

    name = "github_tool"

    def __init__(self) -> None:
        self.calls = 0

    def execute(self, input_data: dict) -> Any:
        self.calls += 1
        result = Mock()
        result.data = {"call_number": self.calls, "repo": input_data.get("repo_name")}
        return result


@pytest.mark.unit
class TestIssue43SessionStateCleared:
    """Each review must start fresh; within-run memoization still applies."""

    def test_second_review_executes_tool_fresh_instead_of_reusing_cache(self) -> None:
        """Same Orchestrator + same inputs → tool re-executes on second review."""
        tool = CountingTool()
        store = FakeSessionStore()
        orchestrator = Orchestrator(
            tools={"github_tool": tool},
            session_store=cast(SessionStore, store),
        )
        profile_id = "profile-alice"
        profile_data = {
            "github_username": "alice",
            "projects": [{"github_repo": "alice/demo"}],
        }

        first = orchestrator.run(profile_id, profile_data)
        second = orchestrator.run(profile_id, profile_data)

        assert tool.calls == 2
        assert first["tool_results"]["github_tool"]["call_number"] == 1
        assert second["tool_results"]["github_tool"]["call_number"] == 2

    def test_session_store_drops_stale_keys_from_prior_review(self) -> None:
        """Prior Redis tool keys must not survive a later review with a different plan."""
        tool = CountingTool()
        store = FakeSessionStore()
        store.set(
            "profile-alice",
            {"github_tool": {"call_number": 1, "repo": "alice/old-demo"}},
        )
        orchestrator = Orchestrator(
            tools={"github_tool": tool},
            session_store=cast(SessionStore, store),
        )

        orchestrator.run(
            "profile-alice",
            {"resume_text": "Updated resume with new skills"},
        )

        persisted = store.get("profile-alice")
        assert persisted is not None
        assert "github_tool" not in persisted

    def test_within_run_memoization_still_applies(self) -> None:
        """Duplicate tool/input steps in one run still hit ContextManager cache."""
        tool = CountingTool()
        orchestrator = Orchestrator(tools={"github_tool": tool}, session_store=None)
        tool_input = {"github_username": "alice", "repo_name": "alice/demo"}

        first = orchestrator._execute_tool("github_tool", tool_input)
        second = orchestrator._execute_tool("github_tool", tool_input)

        assert tool.calls == 1
        assert first is second

    def test_run_without_session_store_still_clears_context(self) -> None:
        """session_store=None must not crash; context still clears between runs."""
        tool = CountingTool()
        orchestrator = Orchestrator(tools={"github_tool": tool}, session_store=None)
        profile_data = {
            "github_username": "alice",
            "projects": [{"github_repo": "alice/demo"}],
        }

        orchestrator.run("profile-alice", profile_data)
        orchestrator.run("profile-alice", profile_data)

        assert tool.calls == 2
