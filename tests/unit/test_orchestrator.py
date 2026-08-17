"""
Reproduction tests for issue #47:
Agent state isn't persisted across API restarts.

These tests FAIL with the current (buggy) code and should PASS after the fix.
"""

import json
from unittest.mock import MagicMock

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator


def _make_tool(return_value: dict | None = None) -> MagicMock:
    """Return a mock tool whose execute() returns return_value."""
    tool = MagicMock()
    tool.execute.return_value = return_value or {"ok": True}
    return tool


@pytest.mark.unit
class TestOrchestratorStatePersistence:
    """Reproduce issue #47: state is lost when the server restarts mid-run."""

    def _make_session_store(
        self, existing_state: dict | None = None
    ) -> tuple[SessionStore, MagicMock]:
        """Return a SessionStore backed by a mock Redis client."""
        mock_redis = MagicMock()
        if existing_state is not None:
            mock_redis.get.return_value = json.dumps(existing_state).encode()
        else:
            mock_redis.get.return_value = None
        return SessionStore(mock_redis), mock_redis

    # ------------------------------------------------------------------
    # BUG 1: set() is only called once, after ALL tools complete.
    # If the server restarts after tool1 but before the loop ends,
    # tool1's result is lost — nothing was written to Redis yet.
    # ------------------------------------------------------------------
    def test_state_persisted_after_each_tool(self) -> None:
        """
        FAILS with current code.

        After each successful tool execution, session_store.set() should be
        called so that partial progress survives a mid-run restart.
        Currently set() is called only once, at the very end of run().
        """
        session_store, mock_redis = self._make_session_store()

        tool1 = _make_tool({"score": 90})
        tool2 = _make_tool({"score": 80})

        orchestrator = Orchestrator(
            tools={"tool1": tool1, "tool2": tool2},
            session_store=session_store,
        )
        orchestrator._build_plan = MagicMock(  # type: ignore[method-assign]
            return_value=[
                ("tool1", {}),
                ("tool2", {}),
            ]
        )

        orchestrator.run("profile_abc", {})

        # With the fix: setex called once per tool (2 times).
        # Current (buggy) code: called only once at the end → FAILS
        assert mock_redis.setex.call_count == 2, (
            f"Expected 2 Redis writes (one per tool), got "
            f"{mock_redis.setex.call_count}. "
            "BUG: set() is only called after the full loop."
        )

    # ------------------------------------------------------------------
    # BUG 2: Already-completed tools are never skipped on resume.
    # session_state is loaded from Redis but never consulted in the loop.
    # ------------------------------------------------------------------
    def test_completed_tools_skipped_on_resume(self) -> None:
        """
        FAILS with current code.

        When Redis already contains tool1's result (from a previous run that
        was interrupted after tool1 completed), a restarted Orchestrator should
        load that state and skip tool1, running only tool2.
        Currently the loop always runs every tool regardless of saved state.
        """
        existing_state = {"tool1": {"score": 90}}
        session_store, mock_redis = self._make_session_store(existing_state)

        tool1 = _make_tool({"score": 90})
        tool2 = _make_tool({"score": 80})

        orchestrator = Orchestrator(
            tools={"tool1": tool1, "tool2": tool2},
            session_store=session_store,
        )
        orchestrator._build_plan = MagicMock(  # type: ignore[method-assign]
            return_value=[
                ("tool1", {}),
                ("tool2", {}),
            ]
        )

        orchestrator.run("profile_abc", {})

        # tool1 was already persisted — it should be skipped on resume.
        # Current (buggy) code: tool1 is re-run unconditionally → FAILS
        tool1.execute.assert_not_called()
        tool2.execute.assert_called_once()
