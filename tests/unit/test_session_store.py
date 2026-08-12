"""Tests for agent/memory/session_store.py.

SessionStore.delete() became load-bearing with the fix for issue #43 (the
orchestrator now clears the session when a profile has no reviewable
content), so the store's get/set/delete contract is covered directly here
rather than only through the orchestrator.
"""

import json
from unittest.mock import Mock

import pytest

from agent.memory.session_store import SessionStore


@pytest.fixture
def mock_redis() -> Mock:
    """Create a mock Redis client backed by an in-memory dict."""
    store: dict[str, str] = {}
    redis = Mock()
    redis.get = Mock(side_effect=lambda key: store.get(key))
    redis.setex = Mock(side_effect=lambda key, ttl, value: store.__setitem__(key, value))
    redis.delete = Mock(side_effect=lambda key: store.pop(key, None))
    return redis


@pytest.fixture
def session_store(mock_redis: Mock) -> SessionStore:
    """Create a SessionStore backed by the mock Redis client."""
    return SessionStore(mock_redis)


@pytest.mark.unit
class TestSessionStore:
    """Test suite for SessionStore."""

    def test_set_then_get_roundtrips_data(self, session_store: SessionStore) -> None:
        """Data stored is returned unchanged."""
        data = {"readme_scorer": {"score": 90}, "tech_detector": {"languages": ["python"]}}

        session_store.set("abc", data)

        assert session_store.get("abc") == data

    def test_get_missing_session_returns_none(self, session_store: SessionStore) -> None:
        """A session that was never written returns None, not {}."""
        assert session_store.get("never-written") is None

    def test_set_replaces_previous_value(self, session_store: SessionStore) -> None:
        """set() overwrites rather than merging — the orchestrator relies on this."""
        session_store.set("abc", {"skill_extractor": {"skills": ["go"]}})
        session_store.set("abc", {"readme_scorer": {"score": 50}})

        assert session_store.get("abc") == {"readme_scorer": {"score": 50}}

    def test_delete_removes_session(self, session_store: SessionStore) -> None:
        """After delete(), get() reports the session as absent."""
        session_store.set("abc", {"readme_scorer": {"score": 90}})

        session_store.delete("abc")

        assert session_store.get("abc") is None

    def test_delete_missing_session_does_not_raise(self, session_store: SessionStore) -> None:
        """Deleting a session that isn't there is a no-op, not an error."""
        session_store.delete("never-written")

        assert session_store.get("never-written") is None

    def test_keys_are_namespaced(self, session_store: SessionStore, mock_redis: Mock) -> None:
        """Session keys are prefixed so they cannot collide with other Redis users."""
        session_store.set("abc", {"readme_scorer": {"score": 90}})

        key = mock_redis.setex.call_args[0][0]
        assert key == "session:abc"

    def test_set_applies_default_one_hour_ttl(
        self, session_store: SessionStore, mock_redis: Mock
    ) -> None:
        """Sessions expire by default so abandoned state does not live forever."""
        session_store.set("abc", {"readme_scorer": {"score": 90}})

        assert mock_redis.setex.call_args[0][1] == 3600

    def test_set_honors_custom_ttl(self, session_store: SessionStore, mock_redis: Mock) -> None:
        """An explicit ttl_seconds is passed through to Redis."""
        session_store.set("abc", {"readme_scorer": {"score": 90}}, ttl_seconds=60)

        assert mock_redis.setex.call_args[0][1] == 60

    def test_get_returns_none_on_corrupt_json(
        self, session_store: SessionStore, mock_redis: Mock
    ) -> None:
        """Malformed stored data degrades to a cache miss instead of raising."""
        mock_redis.get = Mock(return_value="{not valid json")

        assert session_store.get("abc") is None

    def test_get_returns_none_when_redis_errors(
        self, session_store: SessionStore, mock_redis: Mock
    ) -> None:
        """A Redis outage degrades to a cache miss instead of failing the review."""
        mock_redis.get = Mock(side_effect=ConnectionError("redis is down"))

        assert session_store.get("abc") is None

    def test_set_swallows_redis_errors(self, session_store: SessionStore, mock_redis: Mock) -> None:
        """A failed write is logged, not raised — a review should still complete."""
        mock_redis.setex = Mock(side_effect=ConnectionError("redis is down"))

        session_store.set("abc", {"readme_scorer": {"score": 90}})

    def test_delete_swallows_redis_errors(
        self, session_store: SessionStore, mock_redis: Mock
    ) -> None:
        """A failed delete is logged, not raised."""
        mock_redis.delete = Mock(side_effect=ConnectionError("redis is down"))

        session_store.delete("abc")

    def test_empty_session_is_distinguishable_from_missing_session(
        self, session_store: SessionStore, mock_redis: Mock
    ) -> None:
        """An empty session reads back as {}, while a missing one reads as None.

        The stored payload is the string "{}", which is truthy, so it does
        not take get()'s falsy-payload miss path. The orchestrator still
        prefers delete() over set({}) for an empty plan, to avoid leaving a
        TTL-refreshing placeholder key in Redis.
        """
        session_store.set("abc", {})

        assert json.loads(mock_redis.setex.call_args[0][2]) == {}
        assert session_store.get("abc") == {}
        assert session_store.get("other") is None
