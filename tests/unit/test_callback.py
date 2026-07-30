"""Callback registration tests: registering and deleting a callback URL. This does not test or
provide a client implementation of the callback handling itself, but client_callback_server.py
under docs/examples shows a barebones example of how the callback URL can await for notifications
and handle deduplication.
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from core.services.webhook_service import (
    CallbackAlreadyExistsError,
    delete_callback_url,
    set_callback_url,
)


@pytest.mark.unit
class TestCallback:
    """Test suite for registering/deleting a callback."""

    @pytest.fixture
    def user_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def profile_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.delete = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_callback(self, user_id: UUID, profile_id: UUID) -> Mock:
        """Create a mock Callback object registered for user_id/profile_id."""
        callback = Mock()
        callback.id = str(uuid4())
        callback.user_id = str(user_id)
        callback.profile_id = str(profile_id)
        callback.url = "https://client.example.com/callback"
        return callback

    @pytest.mark.asyncio
    async def test_register_callback(
        self, mock_db_session: AsyncMock, user_id: UUID, profile_id: UUID
    ) -> None:
        """Test registering a callback URL for a profile that doesn't already have one."""
        url = "https://client.example.com/callback"

        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = Mock()
        callback_result = Mock()
        callback_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(side_effect=[profile_result, callback_result])

        result = await set_callback_url(mock_db_session, user_id, profile_id, url)

        added_callback = mock_db_session.add.call_args[0][0]
        assert added_callback.user_id == str(user_id)
        assert added_callback.profile_id == str(profile_id)
        assert added_callback.url == url
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        assert result is added_callback

    @pytest.mark.asyncio
    async def test_register_callback_already_exists_raises(
        self, mock_db_session: AsyncMock, mock_callback: Mock, user_id: UUID, profile_id: UUID
    ) -> None:
        """Test registering a second callback for a profile that already has one is rejected."""
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = Mock()
        callback_result = Mock()
        callback_result.scalars.return_value.first.return_value = mock_callback
        mock_db_session.execute = AsyncMock(side_effect=[profile_result, callback_result])

        with pytest.raises(CallbackAlreadyExistsError):
            await set_callback_url(mock_db_session, user_id, profile_id, mock_callback.url)

        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_callback(
        self, mock_db_session: AsyncMock, mock_callback: Mock, user_id: UUID, profile_id: UUID
    ) -> None:
        """Test deleting a registered callback removes it and commits."""
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_callback
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await delete_callback_url(mock_db_session, user_id, profile_id)

        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_callback)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_callback_returns_false_when_not_found(
        self, mock_db_session: AsyncMock, user_id: UUID, profile_id: UUID
    ) -> None:
        """Test deleting a callback that isn't registered is a no-op returning False."""
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await delete_callback_url(mock_db_session, user_id, profile_id)

        assert result is False
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()
