"""Tests for agent state persistence across restarts (issue #47)."""

import json
from unittest.mock import Mock

import pytest
import redis

from agent.memory.context_manager import ContextManager
from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import ToolResult


class FakeSessionStore(SessionStore):
    """In-memory stand-in for the Redis SessionStore.

    JSON round-trips values on set/get so serialization bugs surface the
    same way they would against real Redis.
    """

    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def get(self, session_id: str) -> dict | None:
        raw = self.data.get(f"session:{session_id}")
        if not raw:
            return None
        parsed: dict = json.loads(raw)
        return parsed

    def set(self, session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
        self.data[f"session:{session_id}"] = json.dumps(data)

    def delete(self, session_id: str) -> None:
        self.data.pop(f"session:{session_id}", None)


class SpySessionStore(FakeSessionStore):
    """FakeSessionStore that records every write for assertions."""

    def __init__(self) -> None:
        super().__init__()
        self.writes: list[tuple[str, dict]] = []

    def set(self, session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
        self.writes.append((session_id, json.loads(json.dumps(data))))
        super().set(session_id, data, ttl_seconds)


def make_tool(name: str, data: dict) -> Mock:
    """Create a mock tool returning a successful ToolResult."""
    tool = Mock()
    tool.name = name
    tool.execute = Mock(return_value=ToolResult(success=True, data=data))
    return tool


@pytest.mark.unit
class TestContextManagerPersistence:
    """ContextManager write-through persistence and hydration."""

    def test_store_writes_through_to_session_store(self) -> None:
        store = FakeSessionStore()
        context = ContextManager(session_store=store, session_id="p1")

        result = ToolResult(success=True, data={"score": 0.9})
        context.store_tool_result("readme_scorer", "abc123", result)

        persisted = store.get("p1:context")
        assert persisted is not None
        assert "readme_scorer:abc123" in persisted

    def test_new_instance_hydrates_persisted_results(self) -> None:
        store = FakeSessionStore()
        first = ContextManager(session_store=store, session_id="p1")
        first.store_tool_result(
            "readme_scorer",
            "abc123",
            ToolResult(success=True, data={"score": 0.9}),
        )

        # Simulate restart: fresh instance, same store
        second = ContextManager(session_store=store, session_id="p1")
        cached = second.get_tool_result("readme_scorer", "abc123")

        assert isinstance(cached, ToolResult)
        assert cached.success is True
        assert cached.data == {"score": 0.9}
        assert cached.error is None

    def test_sessions_are_isolated_by_id(self) -> None:
        store = FakeSessionStore()
        first = ContextManager(session_store=store, session_id="p1")
        first.store_tool_result(
            "readme_scorer",
            "abc123",
            ToolResult(success=True, data={"score": 0.9}),
        )

        other = ContextManager(session_store=store, session_id="p2")
        assert other.get_tool_result("readme_scorer", "abc123") is None

    def test_non_serializable_result_is_skipped_without_error(self) -> None:
        store = FakeSessionStore()
        context = ContextManager(session_store=store, session_id="p1")

        context.store_tool_result("weird_tool", "h1", object())
        context.store_tool_result(
            "readme_scorer",
            "h2",
            ToolResult(success=True, data={"score": 0.9}),
        )

        # In-memory cache still holds both
        assert context.get_tool_result("weird_tool", "h1") is not None

        # Only the serializable one survives a restart
        rehydrated = ContextManager(session_store=store, session_id="p1")
        assert rehydrated.get_tool_result("weird_tool", "h1") is None
        assert rehydrated.get_tool_result("readme_scorer", "h2") is not None

    def test_clear_persisted_removes_context(self) -> None:
        store = FakeSessionStore()
        context = ContextManager(session_store=store, session_id="p1")
        context.store_tool_result(
            "readme_scorer",
            "abc123",
            ToolResult(success=True, data={"score": 0.9}),
        )

        context.clear_persisted()
        assert store.get("p1:context") is None

    def test_no_store_behaves_as_pure_in_memory_cache(self) -> None:
        context = ContextManager()
        result = ToolResult(success=True, data={"score": 0.9})
        context.store_tool_result("readme_scorer", "abc123", result)
        assert context.get_tool_result("readme_scorer", "abc123") is result

    def test_unexpected_persisted_payload_starts_cold(self) -> None:
        store = FakeSessionStore()
        # Something other than this class wrote the key
        store.data["session:p1:context"] = json.dumps(["not", "a", "dict"])

        context = ContextManager(session_store=store, session_id="p1")

        assert context.get_all_results() == {}

    def test_redis_failure_on_hydrate_is_not_fatal(self) -> None:
        redis_client = Mock()
        redis_client.get = Mock(side_effect=redis.ConnectionError("redis is down"))
        store = SessionStore(redis_client)

        context = ContextManager(session_store=store, session_id="p1")

        assert context.get_all_results() == {}

    def test_redis_failure_on_write_leaves_memory_cache_usable(self) -> None:
        redis_client = Mock()
        redis_client.get = Mock(return_value=None)
        redis_client.setex = Mock(side_effect=redis.ConnectionError("redis is down"))
        store = SessionStore(redis_client)

        context = ContextManager(session_store=store, session_id="p1")
        result = ToolResult(success=True, data={"score": 0.9})
        context.store_tool_result("readme_scorer", "abc123", result)

        # Write failed, but the current process keeps its cache
        assert context.get_tool_result("readme_scorer", "abc123") is result


@pytest.mark.unit
class TestOrchestratorResume:
    """Orchestrator checkpointing and resume after a simulated restart."""

    @pytest.fixture
    def profile_data(self) -> dict:
        return {
            "files": ["app.py", "requirements.txt"],
            "readme_content": "# Project\nA sample project.",
        }

    @pytest.fixture
    def tools(self) -> dict:
        return {
            "tech_detector": make_tool("tech_detector", {"stack": ["python"]}),
            "readme_scorer": make_tool("readme_scorer", {"score": 0.8}),
            "market_analyzer": make_tool("market_analyzer", {"demand": "high"}),
        }

    def test_progress_checkpointed_during_run(self, tools: dict, profile_data: dict) -> None:
        store = SpySessionStore()

        orchestrator = Orchestrator(tools=tools, session_store=store)
        orchestrator.run("p1", profile_data)

        # One checkpoint per plan step, before the final write
        checkpoints = [data for sid, data in store.writes if sid == "p1"]
        in_progress = [c for c in checkpoints if "_in_progress" in c]
        assert len(in_progress) == 3
        assert in_progress[0]["_in_progress"]["completed_steps"] == 1
        assert in_progress[0]["_in_progress"]["total_steps"] == 3
        assert "tech_detector" in in_progress[0]["_in_progress"]["partial_results"]

        # Final state has results and no in-progress marker
        final = store.get("p1")
        assert final is not None
        assert "_in_progress" not in final
        assert final["readme_scorer"] == {"score": 0.8}

    def test_interrupted_run_resumes_without_reexecuting_tools(
        self, tools: dict, profile_data: dict
    ) -> None:
        store = FakeSessionStore()

        # First run dies on the second tool, as if the process was killed
        tools["readme_scorer"].execute.side_effect = KeyboardInterrupt
        orchestrator = Orchestrator(tools=tools, session_store=store)
        with pytest.raises(KeyboardInterrupt):
            orchestrator.run("p1", profile_data)

        assert tools["tech_detector"].execute.call_count == 1
        # The completed tool's result was persisted before the crash
        assert store.get("p1:context") is not None

        # "Restart": new orchestrator, tool no longer failing
        tools["readme_scorer"].execute.side_effect = None
        resumed = Orchestrator(tools=tools, session_store=store)
        output = resumed.run("p1", profile_data)

        # Completed work was not redone; remaining tools ran once each
        assert tools["tech_detector"].execute.call_count == 1
        assert tools["readme_scorer"].execute.call_count == 2  # crash + resume
        assert tools["market_analyzer"].execute.call_count == 1

        assert output["tool_results"]["tech_detector"] == {"stack": ["python"]}
        assert output["tool_results"]["readme_scorer"] == {"score": 0.8}

        # Completed session cleans up its in-progress context
        assert store.get("p1:context") is None

    def test_run_without_session_store_still_works(self, tools: dict, profile_data: dict) -> None:
        orchestrator = Orchestrator(tools=tools)
        output = orchestrator.run("p1", profile_data)

        assert output["tool_results"]["tech_detector"] == {"stack": ["python"]}
        assert len(output["tool_results"]) == 3

    def test_run_completes_when_redis_is_down(self, tools: dict, profile_data: dict) -> None:
        redis_client = Mock()
        redis_client.get = Mock(side_effect=redis.ConnectionError("redis is down"))
        redis_client.setex = Mock(side_effect=redis.ConnectionError("redis is down"))
        redis_client.delete = Mock(side_effect=redis.ConnectionError("redis is down"))
        store = SessionStore(redis_client)

        orchestrator = Orchestrator(tools=tools, session_store=store)
        output = orchestrator.run("p1", profile_data)

        # Checkpointing degrades to the old in-memory behavior instead of
        # failing the run it exists to protect
        assert len(output["tool_results"]) == 3
        assert output["tool_results"]["readme_scorer"] == {"score": 0.8}
