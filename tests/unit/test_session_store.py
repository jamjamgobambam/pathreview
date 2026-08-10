"""Unit tests for SessionStore (agent/memory/session_store.py).

Covers the get/set/delete round-trip, confirms delete() actually removes the
key (the method the #43 fix activates), the Redis key/TTL contract, and the
log-and-swallow behavior the orchestrator relies on when Redis errors.
"""

import json
from unittest.mock import Mock

import pytest

from agent.memory.session_store import SessionStore


class FakeRedis:
    """Minimal in-memory stand-in for the Redis calls SessionStore makes."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


@pytest.mark.unit
class TestSessionStore:
    """Round-trip and contract tests for the Redis-backed SessionStore."""

    @pytest.fixture
    def fake_redis(self) -> FakeRedis:
        return FakeRedis()

    @pytest.fixture
    def store(self, fake_redis: FakeRedis) -> SessionStore:
        # FakeRedis implements only the calls SessionStore uses; the real
        # constructor is typed for redis.Redis, so silence that arg-type check.
        return SessionStore(fake_redis)  # type: ignore[arg-type]

    @pytest.fixture
    def mock_redis(self) -> Mock:
        return Mock()

    def test_set_then_get_round_trips_dict(self, store: SessionStore) -> None:
        data = {"readme_scorer": {"score": 95}, "nested": {"a": [1, 2, 3]}}
        store.set("user1", data)
        assert store.get("user1") == data

    def test_get_returns_none_for_missing_key(self, store: SessionStore) -> None:
        assert store.get("never-written") is None

    def test_delete_removes_key(self, store: SessionStore) -> None:
        store.set("user1", {"x": 1})
        assert store.get("user1") == {"x": 1}

        store.delete("user1")
        assert store.get("user1") is None

    def test_delete_missing_key_is_noop(self, store: SessionStore) -> None:
        # First-ever review: delete() on a key that was never set must not raise.
        store.delete("never-written")
        assert store.get("never-written") is None

    def test_set_overwrites_previous_state(self, store: SessionStore) -> None:
        # setex fully replaces the value; a second set() does not merge.
        store.set("user1", {"readme_scorer": {"score": 95}})
        store.set("user1", {"skill_extractor": {"skills": ["Python"]}})
        assert store.get("user1") == {"skill_extractor": {"skills": ["Python"]}}

    def test_set_uses_session_prefix_and_default_ttl(self, mock_redis: Mock) -> None:
        store = SessionStore(mock_redis)  # type: ignore[arg-type]
        store.set("user1", {"x": 1})

        mock_redis.setex.assert_called_once()
        key, ttl, payload = mock_redis.setex.call_args[0]
        assert key == "session:user1"
        assert ttl == 3600
        assert json.loads(payload) == {"x": 1}

    def test_set_honors_custom_ttl(self, mock_redis: Mock) -> None:
        store = SessionStore(mock_redis)  # type: ignore[arg-type]
        store.set("user1", {"x": 1}, ttl_seconds=60)
        assert mock_redis.setex.call_args[0][1] == 60

    def test_delete_uses_session_prefixed_key(self, mock_redis: Mock) -> None:
        store = SessionStore(mock_redis)  # type: ignore[arg-type]
        store.delete("user1")
        mock_redis.delete.assert_called_once_with("session:user1")

    def test_get_returns_none_on_invalid_json(self, mock_redis: Mock) -> None:
        mock_redis.get = Mock(return_value="{ not valid json")
        store = SessionStore(mock_redis)  # type: ignore[arg-type]
        assert store.get("user1") is None

    def test_set_swallows_redis_error(self, mock_redis: Mock) -> None:
        mock_redis.setex = Mock(side_effect=Exception("redis down"))
        store = SessionStore(mock_redis)  # type: ignore[arg-type]
        # Must not raise -- the orchestrator relies on this to keep returning.
        store.set("user1", {"x": 1})

    def test_delete_swallows_redis_error(self, mock_redis: Mock) -> None:
        mock_redis.delete = Mock(side_effect=Exception("redis down"))
        store = SessionStore(mock_redis)  # type: ignore[arg-type]
        store.delete("user1")

    def test_get_swallows_redis_error(self, mock_redis: Mock) -> None:
        mock_redis.get = Mock(side_effect=Exception("redis down"))
        store = SessionStore(mock_redis)  # type: ignore[arg-type]
        assert store.get("user1") is None
