"""Tests for orchestrator.py"""

import json
from typing import Any
from unittest.mock import Mock, patch

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import ToolResult

Plan = list[tuple[str, dict]]


class FakeSessionStore(SessionStore):
    """In-memory stand-in for the Redis-backed SessionStore.

    Round-trips data through json (like the real store does) so tests catch
    bugs that only show up after a real serialize/deserialize cycle, and
    records every set() call so tests can assert checkpointing happens
    incrementally rather than once at the end.
    """

    def __init__(self) -> None:
        super().__init__(redis_client=Mock())
        self._data: dict[str, dict] = {}
        self.set_calls: list[dict] = []

    def get(self, session_id: str) -> dict | None:
        return self._data.get(session_id)

    def set(self, session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
        snapshot = json.loads(json.dumps(data))
        self._data[session_id] = snapshot
        self.set_calls.append(snapshot)


@pytest.fixture(autouse=True)
def no_retry_sleep() -> Any:
    """Skip real sleeps in the retry-with-backoff decorator during tests."""
    with patch("agent.error_handling.time.sleep"):
        yield


def make_tool(name: str, result: dict | None = None, error: Exception | None = None) -> Mock:
    tool = Mock()
    tool.name = name
    if error is not None:
        tool.execute = Mock(side_effect=error)
    else:
        tool.execute = Mock(return_value=ToolResult(success=True, data=result or {}))
    return tool


@pytest.mark.unit
class TestOrchestratorCheckpointing:
    """Test suite for orchestrator progress persistence across restarts."""

    @pytest.fixture
    def session_store(self) -> FakeSessionStore:
        return FakeSessionStore()

    def test_progress_is_checkpointed_after_each_tool_not_only_at_the_end(
        self, session_store: FakeSessionStore
    ) -> None:
        """Regression test: checkpointing used to happen once, after the
        whole loop finished, which meant a mid-loop crash lost everything.
        Redis should be written to after every tool completes."""
        tools = {
            "tool_a": make_tool("tool_a", result={"result": "a"}),
            "tool_b": make_tool("tool_b", result={"result": "b"}),
        }
        plan: Plan = [("tool_a", {}), ("tool_b", {})]

        orchestrator = Orchestrator(tools, session_store=session_store)
        with patch.object(orchestrator, "_build_plan", return_value=plan):
            orchestrator.run("profile-1", {})

        # One checkpoint per tool, not a single checkpoint at the end.
        assert len(session_store.set_calls) == 2
        assert session_store.set_calls[0] == {"tool_a": {"result": "a"}}
        assert session_store.set_calls[1] == {
            "tool_a": {"result": "a"},
            "tool_b": {"result": "b"},
        }

    def test_restart_mid_review_resumes_without_rerunning_completed_tools(
        self, session_store: FakeSessionStore
    ) -> None:
        """Simulates the exact bug from issue #47: a long review spanning
        multiple repos/tools gets interrupted by a server restart partway
        through. A fresh Orchestrator sharing the same session_store (the
        only thing that survives a restart) should pick up where the
        previous one left off, not repeat completed work."""
        tools = {
            "tool_a": make_tool("tool_a", result={"result": "a"}),
            "tool_b": make_tool("tool_b", result={"result": "b"}),
            "tool_c": make_tool("tool_c", result={"result": "c"}),
        }
        full_plan: Plan = [("tool_a", {}), ("tool_b", {}), ("tool_c", {})]

        # First "process": only gets through tool_a and tool_b before the
        # restart happens (modeled as simply never reaching tool_c).
        orchestrator_before_restart = Orchestrator(tools, session_store=session_store)
        with patch.object(orchestrator_before_restart, "_build_plan", return_value=full_plan[:2]):
            orchestrator_before_restart.run("profile-1", {})

        assert tools["tool_a"].execute.call_count == 1
        assert tools["tool_b"].execute.call_count == 1
        assert tools["tool_c"].execute.call_count == 0

        # "Restart": brand new Orchestrator instance, sharing only the
        # session_store, now sees the full plan (including the tool that
        # never got a chance to run).
        orchestrator_after_restart = Orchestrator(tools, session_store=session_store)
        with patch.object(orchestrator_after_restart, "_build_plan", return_value=full_plan):
            result = orchestrator_after_restart.run("profile-1", {})

        # tool_a and tool_b already succeeded and were checkpointed before
        # the restart -> must not be re-executed.
        assert tools["tool_a"].execute.call_count == 1
        assert tools["tool_b"].execute.call_count == 1
        # tool_c never ran -> must execute now.
        assert tools["tool_c"].execute.call_count == 1

        assert result["tool_results"] == {
            "tool_a": {"result": "a"},
            "tool_b": {"result": "b"},
            "tool_c": {"result": "c"},
        }

    def test_previously_failed_tool_is_retried_on_resume(
        self, session_store: FakeSessionStore
    ) -> None:
        """A tool that failed before the restart is not "done" and should
        be retried, not skipped like a successful checkpoint."""
        # Seed the store as if a previous run recorded tool_a succeeding
        # and tool_b failing.
        session_store.set(
            "profile-1",
            {
                "tool_a": {"result": "a"},
                "tool_b": {"error": "simulated crash", "success": False},
            },
        )

        tools = {
            "tool_a": make_tool("tool_a", result={"result": "a"}),
            "tool_b": make_tool("tool_b", result={"result": "b-retry-succeeded"}),
        }
        plan: Plan = [("tool_a", {}), ("tool_b", {})]

        orchestrator = Orchestrator(tools, session_store=session_store)
        with patch.object(orchestrator, "_build_plan", return_value=plan):
            result = orchestrator.run("profile-1", {})

        # tool_a was already done -> skipped.
        assert tools["tool_a"].execute.call_count == 0
        # tool_b previously failed -> retried, and succeeds this time.
        assert tools["tool_b"].execute.call_count == 1
        assert result["tool_results"]["tool_b"] == {"result": "b-retry-succeeded"}

    def test_no_session_store_runs_without_persistence(self) -> None:
        """Orchestrator without a session_store should still run every tool
        normally; persistence is optional, not required for correctness."""
        tools = {
            "tool_a": make_tool("tool_a", result={"result": "a"}),
            "tool_b": make_tool("tool_b", result={"result": "b"}),
        }
        plan: Plan = [("tool_a", {}), ("tool_b", {})]

        orchestrator = Orchestrator(tools, session_store=None)
        with patch.object(orchestrator, "_build_plan", return_value=plan):
            result = orchestrator.run("profile-1", {})

        assert result["tool_results"] == {
            "tool_a": {"result": "a"},
            "tool_b": {"result": "b"},
        }
