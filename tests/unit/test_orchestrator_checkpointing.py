"""Tests for Orchestrator per-step checkpointing and resume behavior (issue #47)."""

from unittest.mock import Mock

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult


class FakeRedis:
    """In-memory stand-in for redis.Redis, backed by a plain dict.

    Implements just the subset of the redis-py API that SessionStore uses,
    so tests exercise the real SessionStore (including its JSON
    serialization) instead of mocking it away. It does not subclass
    redis.Redis, so constructing a SessionStore with one needs a type:
    ignore at each call site below.
    """

    def __init__(self) -> None:
        self.store: dict = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


class CountingTool(BaseTool):
    """Fake tool that records how many times it was executed."""

    def __init__(self, name: str, fail_times: int = 0):
        self.name = name
        self.description = f"counting tool {name}"
        self.call_count = 0
        self.fail_times = fail_times

    def execute(self, input_data: dict) -> ToolResult:
        self.call_count += 1
        if self.call_count <= self.fail_times:
            raise RuntimeError(f"{self.name} simulated failure")
        return ToolResult(success=True, data={"tool": self.name, "call": self.call_count})


@pytest.mark.unit
class TestOrchestratorCheckpointing:
    """Test suite for per-step checkpointing and resume behavior."""

    @pytest.fixture
    def fake_redis(self) -> FakeRedis:
        return FakeRedis()

    @pytest.fixture
    def session_store(self, fake_redis: FakeRedis) -> SessionStore:
        return SessionStore(fake_redis)  # type: ignore[arg-type]

    def _orchestrator(self, tools: dict, session_store: SessionStore) -> Orchestrator:
        """Build an Orchestrator with a fixed plan, bypassing _build_plan's
        profile_data-shape logic so tests can drive an exact plan directly."""
        orch = Orchestrator(tools=tools, session_store=session_store)
        orch._build_plan = lambda profile_data: [(name, {}) for name in tools]  # type: ignore[method-assign]
        return orch

    def test_checkpoints_after_each_step_not_only_at_end(
        self, session_store: SessionStore, fake_redis: FakeRedis
    ) -> None:
        """Redis should hold the first step's result while the second step is
        still running, proving the checkpoint isn't deferred to the end of
        the whole plan (the old, buggy behavior)."""
        seen_during_second_step: dict = {}

        class SpyTool(CountingTool):
            def execute(self, input_data: dict) -> ToolResult:
                # Snapshot Redis state as observed while tool_b is running,
                # i.e. after tool_a's loop iteration (and its checkpoint
                # write) has already completed, but before tool_b's own
                # checkpoint write happens.
                seen_during_second_step["state"] = session_store.get("profile-1")
                return super().execute(input_data)

        tools = {"tool_a": CountingTool("tool_a"), "tool_b": SpyTool("tool_b")}
        orch = self._orchestrator(tools, session_store)

        orch.run("profile-1", {})

        state = seen_during_second_step["state"]
        assert state is not None
        assert any(key.startswith("tool_a:") for key in state["completed"])
        assert not any(key.startswith("tool_b:") for key in state["completed"])

    def test_resume_skips_already_completed_steps(self, session_store: SessionStore) -> None:
        """A tool that already succeeded should not be re-executed on a resumed run."""
        tool_a = CountingTool("tool_a")
        # Exhausts _execute_with_timeout's internal retry budget (max_retries=2)
        # within the first run() call, so the step genuinely fails and is
        # never checkpointed -- simulating a step that hadn't finished when
        # the process was interrupted.
        tool_b = CountingTool("tool_b", fail_times=2)

        tools = {"tool_a": tool_a, "tool_b": tool_b}
        orch = self._orchestrator(tools, session_store)

        first = orch.run("profile-1", {})
        assert first["tool_results"]["tool_a"] == {"tool": "tool_a", "call": 1}
        assert first["tool_results"]["tool_b"]["success"] is False
        assert tool_a.call_count == 1
        assert tool_b.call_count == 2

        # Simulate a restart: fresh Orchestrator instance (fresh in-memory
        # ContextManager), same session_store (same "Redis").
        resumed_orch = self._orchestrator(tools, session_store)
        second = resumed_orch.run("profile-1", {})

        # tool_a must NOT run again -- its checkpointed result is reused.
        assert tool_a.call_count == 1
        assert second["tool_results"]["tool_a"] == {"tool": "tool_a", "call": 1}

        # tool_b, which never checkpointed (it failed), retries and succeeds
        # on the third call overall (its first successful attempt).
        assert tool_b.call_count == 3
        assert second["tool_results"]["tool_b"] == {"tool": "tool_b", "call": 3}

    def test_different_input_is_not_treated_as_already_done(
        self, session_store: SessionStore
    ) -> None:
        """Same tool name with different input must not reuse a stale checkpoint."""
        tool = CountingTool("tool_a")
        orch = Orchestrator(tools={"tool_a": tool}, session_store=session_store)
        orch._build_plan = lambda profile_data: [("tool_a", {"x": 1})]  # type: ignore[method-assign]

        orch.run("profile-1", {})
        assert tool.call_count == 1

        orch._build_plan = lambda profile_data: [("tool_a", {"x": 2})]  # type: ignore[method-assign]
        orch.run("profile-1", {})

        # Different input hash -> treated as a new step, not a cache hit.
        assert tool.call_count == 2

    def test_checkpoint_write_failure_is_logged_not_silent(
        self, session_store: SessionStore
    ) -> None:
        """A failed Redis write during checkpointing should be surfaced via logging,
        not swallowed without any signal, and should not crash the run."""
        session_store.set = Mock(return_value=False)  # type: ignore[method-assign]
        tool = CountingTool("tool_a")
        orch = self._orchestrator({"tool_a": tool}, session_store)

        with pytest.MonkeyPatch.context() as mp:
            logged: dict = {}
            mp.setattr(
                "agent.orchestrator.logger.error",
                lambda event, **kwargs: logged.setdefault(event, kwargs),
            )
            result = orch.run("profile-1", {})

        assert "checkpoint_write_failed" in logged
        assert result["tool_results"]["tool_a"] == {"tool": "tool_a", "call": 1}

    def test_uninterrupted_run_matches_result_of_interrupted_then_resumed_run(
        self, session_store: SessionStore
    ) -> None:
        """An interrupted-then-resumed run should end up with the same final
        results as a run that never got interrupted in the first place."""
        clean_tools = {"tool_a": CountingTool("tool_a"), "tool_b": CountingTool("tool_b")}
        clean_orch = self._orchestrator(clean_tools, SessionStore(FakeRedis()))  # type: ignore[arg-type]
        clean_result = clean_orch.run("profile-1", {})

        interrupted_tools = {"tool_a": CountingTool("tool_a"), "tool_b": CountingTool("tool_b")}
        interrupted_orch = self._orchestrator(
            {"tool_a": interrupted_tools["tool_a"]}, session_store
        )
        interrupted_orch.run("profile-1", {})

        resumed_orch = self._orchestrator(interrupted_tools, session_store)
        resumed_result = resumed_orch.run("profile-1", {})

        assert resumed_result["tool_results"] == clean_result["tool_results"]
        assert interrupted_tools["tool_a"].call_count == 1
