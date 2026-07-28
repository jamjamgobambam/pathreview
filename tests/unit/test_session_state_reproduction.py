"""Reproduction for issue #47: review sessions collide for one profile."""

from typing import Any, cast

import redis

from agent.memory.session_store import SessionStore


class FakeRedis:
    """Minimal Redis double for reproducing the key collision without Docker."""

    def __init__(self) -> None:
        self.values = {}

    def get(self, key: str) -> Any:
        return self.values.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


def test_second_review_overwrites_first_review_session() -> None:
    """Two reviews for one profile must not share one persisted session key.

    This currently fails because the orchestration path passes profile_id to
    SessionStore instead of a review/session identifier.
    """
    fake_redis = FakeRedis()
    store = SessionStore(cast("redis.Redis", fake_redis))

    store.set("profile-42", {"review_id": "review-1", "tool_result": "old"})
    store.set("profile-42", {"review_id": "review-2", "tool_result": "new"})

    assert store.get("review-1") == {
        "review_id": "review-1",
        "tool_result": "old",
    }
