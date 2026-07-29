"""Reproduction tests for issue #43 — stale agent state between reviews.

These tests document the *current* buggy behavior. Week 9 will invert the
assertions once Orchestrator clears session/context state at the start of
each run.
"""

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
class TestIssue43SessionStateReproduction:
    """Prove issue #43 locally without needing the full UI stack."""

    def test_second_review_reuses_context_cache_instead_of_rerunning_tools(self) -> None:
        """Same Orchestrator + same inputs → tool only executes once (bug).

        ContextManager lives for the Orchestrator lifetime and memoizes by
        tool_name + input hash. A second review for the same profile therefore
        hits the cache and never re-calls the tool — even if the underlying
        GitHub/repo data changed outside of the hashed input fields.
        """
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

        # Current buggy behavior (reproduction of #43):
        assert tool.calls == 1
        assert first["tool_results"]["github_tool"] == second["tool_results"]["github_tool"]
        assert second["tool_results"]["github_tool"]["call_number"] == 1

    def test_session_store_keeps_stale_keys_from_prior_review(self) -> None:
        """session_state.update() merges old Redis keys into later reviews.

        If review 1 ran github_tool and review 2 only has resume text (no
        github), the old github_tool payload still remains in the session.
        """
        tool = CountingTool()
        store = FakeSessionStore()
        # Seed a prior review's cached tool result directly in the store.
        store.set(
            "profile-alice",
            {"github_tool": {"call_number": 1, "repo": "alice/old-demo"}},
        )
        orchestrator = Orchestrator(
            tools={"github_tool": tool},
            session_store=cast(SessionStore, store),
        )

        # Second review has no github projects — only resume text for skill_extractor.
        # skill_extractor is not registered, so the plan may be empty / fail tools;
        # we only care that prior session keys survive the merge in run().
        orchestrator.run(
            "profile-alice",
            {"resume_text": "Updated resume with new skills"},
        )

        persisted = store.get("profile-alice")
        assert persisted is not None
        # Current buggy behavior: prior github_tool entry is still present.
        assert "github_tool" in persisted
        assert persisted["github_tool"]["repo"] == "alice/old-demo"
