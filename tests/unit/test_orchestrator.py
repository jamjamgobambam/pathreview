"""Tests for review-scoped agent orchestration state."""

from typing import TYPE_CHECKING, Any, cast

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator

if TYPE_CHECKING:
    import redis


class FakeRedis:
    """Minimal Redis double for session key assertions."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        del ttl_seconds
        self.values[key] = value


class FakeTool:
    """Tool double returning a stable result."""

    name = "fake_tool"

    def execute(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        return {"profile": tool_input["value"]}


@pytest.mark.unit
def test_orchestrator_persists_state_under_review_id() -> None:
    """Separate reviews for one profile write separate session keys."""
    fake_redis = FakeRedis()
    store = SessionStore(cast("redis.Redis", fake_redis))
    orchestrator = Orchestrator({"fake_tool": FakeTool()}, session_store=store)

    from unittest.mock import patch

    with patch.object(
        orchestrator,
        "_build_plan",
        return_value=[("fake_tool", {"value": "first"})],
    ):
        orchestrator.run("profile-42", {"value": "first"}, review_id="review-1")

    with patch.object(
        orchestrator,
        "_build_plan",
        return_value=[("fake_tool", {"value": "second"})],
    ):
        orchestrator.run("profile-42", {"value": "second"}, review_id="review-2")

    assert set(fake_redis.values) == {"session:review-1", "session:review-2"}
    assert store.get("review-1") == {"fake_tool": {"profile": "first"}}
    assert store.get("review-2") == {"fake_tool": {"profile": "second"}}
