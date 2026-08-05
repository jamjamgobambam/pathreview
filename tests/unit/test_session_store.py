"""Tests for session_store.py"""

from unittest.mock import Mock

import pytest

from agent.memory.session_store import SessionStore


@pytest.mark.unit
class TestSessionStore:
    """Test suite for SessionStore."""

    @pytest.fixture
    def mock_redis(self) -> Mock:
        """Create a mock Redis client."""
        return Mock()

    @pytest.fixture
    def store(self, mock_redis: Mock) -> SessionStore:
        """Create a SessionStore instance with mocked Redis."""
        return SessionStore(mock_redis)

    def test_set_returns_true_on_success(self, store: SessionStore, mock_redis: Mock) -> None:
        """Test set() returns True when the Redis write succeeds."""
        mock_redis.setex = Mock()

        result = store.set("session-1", {"a": 1})

        assert result is True

    def test_set_returns_false_on_redis_error(self, store: SessionStore, mock_redis: Mock) -> None:
        """Test set() returns False (not an exception) when Redis errors."""
        mock_redis.setex = Mock(side_effect=Exception("Redis unavailable"))

        result = store.set("session-1", {"a": 1})

        assert result is False

    def test_set_uses_single_setex_call(self, store: SessionStore, mock_redis: Mock) -> None:
        """Test the full value is written in one atomic SETEX call, so a
        crash mid-write can't leave a partially-written value in Redis."""
        mock_redis.setex = Mock()

        store.set("session-1", {"a": 1}, ttl_seconds=120)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "session:session-1"
        assert call_args[0][1] == 120

    def test_get_returns_none_when_write_never_happened(
        self, store: SessionStore, mock_redis: Mock
    ) -> None:
        """Test get() behaves correctly for a session that was never stored."""
        mock_redis.get = Mock(return_value=None)

        result = store.get("session-1")

        assert result is None
