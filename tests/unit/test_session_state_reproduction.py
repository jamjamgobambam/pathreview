"""Reproduction for issue #47: review sessions collide for one profile."""

from typing import TYPE_CHECKING, Any, cast

import pytest

from agent.memory.session_store import SessionStore

if TYPE_CHECKING:
    import redis


class FakeRedis:
    """Minimal Redis double for reproducing the key collision without Docker."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key: str) -> Any:
        return self.values.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


@pytest.mark.unit
def test_reviews_for_one_profile_use_separate_session_keys() -> None:
    """Two reviews for one profile must not share persisted session state."""
    fake_redis = FakeRedis()
    store = SessionStore(cast("redis.Redis", fake_redis))

    store.set("review-1", {"review_id": "review-1", "tool_result": "old"})
    store.set("review-2", {"review_id": "review-2", "tool_result": "new"})

    assert store.get("review-1") == {
        "review_id": "review-1",
        "tool_result": "old",
    }
    assert store.get("review-2") == {
        "review_id": "review-2",
        "tool_result": "new",
    }


@pytest.mark.unit
def test_session_store_keeps_review_keys_distinct_for_same_profile() -> None:
    """Review-specific keys remain distinct even when profile data matches."""
    fake_redis = FakeRedis()
    store = SessionStore(cast("redis.Redis", fake_redis))

    store.set("review-1", {"profile_id": "profile-42"})
    store.set("review-2", {"profile_id": "profile-42"})

    assert set(fake_redis.values) == {"session:review-1", "session:review-2"}
