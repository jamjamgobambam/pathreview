"""Tests for agent state persistence across API restarts (Issue #47).

These tests cover the fix that persists the agent's memoized tool-result cache
(``ContextManager``) to Redis via ``SessionStore`` so that a long-running review
survives an API restart instead of losing its progress.
"""

from typing import cast

import pytest
import redis

from agent.memory.context_manager import ContextManager
from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import ToolResult


class FakeRedis:
    """Minimal in-memory stand-in for the Redis client.

    Implements only the operations SessionStore uses (``get``, ``setex``,
    ``delete``), which lets these tests exercise the full persistence round trip
    without a live Redis server. Values are stored as JSON strings, mirroring how
    real Redis returns bytes/strings for ``get``.
    """

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


def _session_store(fake: FakeRedis) -> SessionStore:
    """Build a SessionStore backed by the in-memory FakeRedis."""
    return SessionStore(cast(redis.Redis, fake))


class CountingTool:
    """Tool that records how many times it actually executed."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.execution_count = 0

    def execute(self, input_data: dict) -> ToolResult:
        self.execution_count += 1
        return ToolResult(success=True, data={"tool": self.name, "input": input_data})


@pytest.mark.unit
class TestContextManagerSerialization:
    """Serialization round trip for the memoized cache."""

    def test_tool_result_survives_round_trip(self) -> None:
        """A ToolResult is restored as a ToolResult, not a bare dict."""
        cm = ContextManager()
        original = ToolResult(success=True, data={"score": 0.9}, error=None)
        cm.store_tool_result("readme_scorer", "hash1", original)

        restored = ContextManager()
        restored.from_dict(cm.to_dict())
        result = restored.get_tool_result("readme_scorer", "hash1")

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data == {"score": 0.9}

    def test_plain_dict_result_survives_round_trip(self) -> None:
        """Dict results are preserved across serialization."""
        cm = ContextManager()
        cm.store_tool_result("tech_detector", "hash2", {"languages": ["python"]})

        restored = ContextManager()
        restored.from_dict(cm.to_dict())

        assert restored.get_tool_result("tech_detector", "hash2") == {"languages": ["python"]}

    def test_unserializable_result_is_skipped_not_raised(self) -> None:
        """A non-serializable result is dropped with a warning, not an error."""
        cm = ContextManager()
        cm.store_tool_result("good", "h1", ToolResult(success=True, data={"ok": True}))
        cm.store_tool_result("bad", "h2", object())  # not a dataclass or dict

        serialized = cm.to_dict()

        assert "good:h1" in serialized
        assert "bad:h2" not in serialized

    def test_from_dict_ignores_empty_payload(self) -> None:
        """Restoring from an empty/None payload leaves the cache untouched."""
        cm = ContextManager()
        cm.store_tool_result("keep", "h1", {"value": 1})
        cm.from_dict({})

        assert cm.get_tool_result("keep", "h1") == {"value": 1}


@pytest.mark.unit
class TestSessionStoreCache:
    """SessionStore persists the context cache under its own key."""

    def test_cache_set_and_get_round_trip(self) -> None:
        store = _session_store(FakeRedis())
        payload = {"readme_scorer:h1": {"__kind__": "dict", "value": {"score": 1}}}

        store.set_cache("profile-1", payload)

        assert store.get_cache("profile-1") == payload

    def test_cache_uses_separate_key_from_session(self) -> None:
        """Cache and session data must not overwrite each other."""
        fake = FakeRedis()
        store = _session_store(fake)

        store.set("profile-1", {"github_tool": {"stars": 3}})
        store.set_cache("profile-1", {"github_tool:h1": {"__kind__": "dict", "value": {}}})

        assert "session:profile-1" in fake.store
        assert "cache:profile-1" in fake.store

    def test_get_cache_returns_none_when_absent(self) -> None:
        store = _session_store(FakeRedis())
        assert store.get_cache("missing") is None


@pytest.mark.unit
class TestOrchestratorRestart:
    """End-to-end: cached work survives an Orchestrator restart."""

    def test_cache_lost_without_session_store(self) -> None:
        """Regression guard: with no session store, a restart still re-executes.

        This documents the original bug (Issue #47): an in-memory-only cache is
        empty after re-initialization, so the tool runs again.
        """
        tool = CountingTool("github_tool")
        tools = {"github_tool": tool}
        tool_input = {"repo": "demo"}

        first = Orchestrator(tools=tools)
        first._execute_tool("github_tool", tool_input)
        assert tool.execution_count == 1

        # Simulate restart: brand new Orchestrator, no persistence configured.
        second = Orchestrator(tools=tools)
        second._execute_tool("github_tool", tool_input)
        assert tool.execution_count == 2  # ran again — the bug

    def test_cache_restored_across_restart_with_session_store(self) -> None:
        """The fix: a shared session store lets a new Orchestrator reuse cache.

        A single Redis-backed store is shared between two Orchestrator instances
        (before and after a simulated restart). The second run for the same
        profile must hit the persisted cache and NOT re-execute the tool.
        """
        store = _session_store(FakeRedis())
        tool = CountingTool("github_tool")
        tools = {"github_tool": tool}

        profile_id = "profile-42"
        profile_data = {
            "github_username": "octocat",
            "projects": [{"github_repo": "hello-world"}],
        }

        # First run persists the cache to Redis.
        first = Orchestrator(tools=tools, session_store=store)
        first.run(profile_id, profile_data)
        assert tool.execution_count == 1

        # Simulate an API restart: fresh Orchestrator with an empty in-memory
        # cache, but the same backing store.
        second = Orchestrator(tools=tools, session_store=store)
        assert len(second.context_manager.results) == 0

        second.run(profile_id, profile_data)

        # Tool was not re-executed: the persisted cache was restored and hit.
        assert tool.execution_count == 1

    def test_progress_checkpointed_after_each_tool(self) -> None:
        """Cache is written incrementally so a mid-review restart keeps progress."""
        store = _session_store(FakeRedis())
        tools = {
            "readme_scorer": CountingTool("readme_scorer"),
            "market_analyzer": CountingTool("market_analyzer"),
        }

        orchestrator = Orchestrator(tools=tools, session_store=store)
        orchestrator.run(
            "profile-7",
            {"readme_content": "# Hello"},  # plan: readme_scorer + market_analyzer
        )

        cache = store.get_cache("profile-7")
        assert cache is not None
        # Both tools' results are present in the persisted cache.
        assert any(key.startswith("readme_scorer:") for key in cache)
        assert any(key.startswith("market_analyzer:") for key in cache)
