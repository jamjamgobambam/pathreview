"""Tests for webhook_service.py"""

from collections.abc import Sequence
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import httpx
import pytest

from core.services.webhook_service import (
    CallbackAlreadyExistsError,
    ProfileNotFoundError,
    RetriesExceededError,
    WebhookTimeoutError,
    create_notification,
    delete_callback_url,
    generate_notification_id,
    notify_callback_on_review_completed,
    send_notification,
    set_callback_url,
)


def _async_client(post_side_effect: BaseException | Sequence[object] | object) -> AsyncMock:
    """Build a mock for `async with httpx.AsyncClient() as client` where client.post has the
    given side_effect (a value, an exception, or a list for successive calls)."""
    client = AsyncMock()
    client.post = AsyncMock(side_effect=post_side_effect)
    context_manager = AsyncMock()
    context_manager.__aenter__ = AsyncMock(return_value=client)
    context_manager.__aexit__ = AsyncMock(return_value=False)
    return context_manager


def _response(status_code: int = 200) -> Mock:
    response = Mock()
    response.raise_for_status = Mock()
    response.status_code = status_code
    return response


@pytest.mark.unit
class TestWebhookService:
    """Test suite for webhook_service module."""

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
    def mock_callback(self) -> Mock:
        """Create a mock Callback object."""
        callback = Mock()
        callback.id = str(uuid4())
        callback.user_id = str(uuid4())
        callback.profile_id = str(uuid4())
        callback.url = "https://client.example.com/callback"
        return callback

    @pytest.fixture
    def mock_notification(self) -> Mock:
        """Create a mock Notification object."""
        notification = Mock()
        notification.id = str(uuid4())
        notification.callback_id = str(uuid4())
        notification.review_id = str(uuid4())
        notification.delivery_status = "retry"
        notification.last_sent_at = None
        notification.last_ack_at = None
        return notification

    @pytest.mark.asyncio
    async def test_set_callback_url_success(self, mock_db_session: AsyncMock) -> None:
        """Test set_callback_url creates a Callback when none exists for the profile."""
        user_id = uuid4()
        profile_id = uuid4()
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
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        assert result is added_callback

    @pytest.mark.asyncio
    async def test_set_callback_url_profile_not_owned_raises(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test set_callback_url raises when the profile doesn't belong to user_id."""
        user_id = uuid4()
        profile_id = uuid4()

        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=profile_result)

        with pytest.raises(ProfileNotFoundError):
            await set_callback_url(mock_db_session, user_id, profile_id, "https://example.com/cb")

        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_callback_url_already_exists_raises(
        self, mock_db_session: AsyncMock, mock_callback: Mock
    ) -> None:
        """Test set_callback_url raises when a callback already exists for the profile."""
        user_id = uuid4()
        profile_id = uuid4()

        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = Mock()
        callback_result = Mock()
        callback_result.scalars.return_value.first.return_value = mock_callback
        mock_db_session.execute = AsyncMock(side_effect=[profile_result, callback_result])

        with pytest.raises(CallbackAlreadyExistsError):
            await set_callback_url(mock_db_session, user_id, profile_id, "https://example.com/cb")

        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_callback_url_success(
        self, mock_db_session: AsyncMock, mock_callback: Mock
    ) -> None:
        """Test delete_callback_url deletes and commits when a matching callback is found."""
        user_id = uuid4()
        profile_id = uuid4()

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_callback
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await delete_callback_url(mock_db_session, user_id, profile_id)

        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_callback)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_callback_url_returns_false_when_not_found(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test delete_callback_url returns False when no matching callback exists."""
        user_id = uuid4()
        profile_id = uuid4()

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await delete_callback_url(mock_db_session, user_id, profile_id)

        assert result is False
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()

    def test_generate_notification_id_is_deterministic(self) -> None:
        """Test generate_notification_id returns the same id for the same triple."""
        user_id, profile_id, review_id = str(uuid4()), str(uuid4()), str(uuid4())

        first = generate_notification_id(user_id, profile_id, review_id)
        second = generate_notification_id(user_id, profile_id, review_id)

        assert first == second

    def test_generate_notification_id_differs_across_reviews(self) -> None:
        """Test generate_notification_id returns a different id for a different review_id."""
        user_id, profile_id = str(uuid4()), str(uuid4())

        first = generate_notification_id(user_id, profile_id, str(uuid4()))
        second = generate_notification_id(user_id, profile_id, str(uuid4()))

        assert first != second

    @pytest.mark.asyncio
    async def test_create_notification_creates_new_when_none_exists(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test create_notification inserts a new row when none exists for this id."""
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await create_notification(
            mock_db_session,
            callback_id="callback-1",
            review_id="review-1",
            notification_id="notif-1",
        )

        added_notification = mock_db_session.add.call_args[0][0]
        assert added_notification.id == "notif-1"
        assert added_notification.callback_id == "callback-1"
        assert added_notification.review_id == "review-1"
        assert added_notification.delivery_status == "pending"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result is added_notification

    @pytest.mark.asyncio
    async def test_create_notification_reuses_existing_for_resend(
        self, mock_db_session: AsyncMock, mock_notification: Mock
    ) -> None:
        """Test create_notification reuses the existing row instead of inserting a duplicate."""
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_notification
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await create_notification(
            mock_db_session,
            callback_id="callback-1",
            review_id="review-1",
            notification_id=mock_notification.id,
        )

        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
        assert result == mock_notification

    @pytest.mark.asyncio
    async def test_send_notification_success_first_attempt(
        self, mock_db_session: AsyncMock, mock_notification: Mock
    ) -> None:
        """Test send_notification marks the notification 'success' on the first attempt, posting
        a payload built from the notification's own id/review_id/callback_id."""
        context_manager = _async_client(post_side_effect=[_response(200)])

        with patch("core.services.webhook_service.httpx.AsyncClient", return_value=context_manager):
            await send_notification(mock_db_session, mock_notification, "https://example.com/cb")

        assert mock_notification.delivery_status == "success"
        assert mock_notification.last_ack_at is not None
        mock_db_session.commit.assert_called_once()

        client = context_manager.__aenter__.return_value
        client.post.assert_awaited_once_with(
            "https://example.com/cb",
            json={
                "notification_id": mock_notification.id,
                "review_id": mock_notification.review_id,
                "callback_id": mock_notification.callback_id,
                "event": "review.completed",
            },
        )

    @pytest.mark.asyncio
    async def test_send_notification_retries_then_succeeds(
        self, mock_db_session: AsyncMock, mock_notification: Mock
    ) -> None:
        """Test send_notification retries after a failed attempt and succeeds, reusing a single
        AsyncClient (opened once) across attempts rather than opening one per attempt."""
        context_manager = _async_client(
            post_side_effect=[httpx.ConnectError("boom"), _response(200)]
        )

        with patch("core.services.webhook_service.httpx.AsyncClient", return_value=context_manager):
            await send_notification(mock_db_session, mock_notification, "https://example.com/cb")

        assert mock_notification.delivery_status == "success"
        # One client is opened for the whole call, reused across both post attempts.
        assert context_manager.__aenter__.await_count == 1
        client = context_manager.__aenter__.return_value
        assert client.post.await_count == 2

    @pytest.mark.asyncio
    async def test_send_notification_raises_after_max_attempts(
        self, mock_db_session: AsyncMock, mock_notification: Mock
    ) -> None:
        """Test send_notification raises RetriesExceededError once every attempt fails, still
        reusing a single AsyncClient across all MAX_SEND_ATTEMPTS attempts."""
        context_manager = _async_client(post_side_effect=httpx.ConnectError("boom"))

        with (
            patch("core.services.webhook_service.httpx.AsyncClient", return_value=context_manager),
            pytest.raises(RetriesExceededError),
        ):
            await send_notification(mock_db_session, mock_notification, "https://example.com/cb")

        assert mock_notification.delivery_status == "fail"
        assert context_manager.__aenter__.await_count == 1
        client = context_manager.__aenter__.return_value
        assert client.post.await_count == 3

    @pytest.mark.asyncio
    async def test_send_notification_timeout_raises_retries_exceeded(
        self, mock_db_session: AsyncMock, mock_notification: Mock
    ) -> None:
        """Test send_notification wraps a timeout on every attempt as RetriesExceededError."""
        context_manager = _async_client(post_side_effect=httpx.TimeoutException("timed out"))

        with (
            patch("core.services.webhook_service.httpx.AsyncClient", return_value=context_manager),
            pytest.raises(RetriesExceededError) as exc_info,
        ):
            await send_notification(mock_db_session, mock_notification, "https://example.com/cb")

        assert isinstance(exc_info.value.__cause__, WebhookTimeoutError)
        assert mock_notification.delivery_status == "fail"

    @pytest.mark.asyncio
    async def test_notify_callback_on_review_completed_success(
        self, mock_db_session: AsyncMock, mock_callback: Mock
    ) -> None:
        """Test notify_callback_on_review_completed creates and sends a notification using the
        callback_id/callback_url passed in by the caller, without re-querying Callback."""
        session_cm = AsyncMock()
        session_cm.__aenter__ = AsyncMock(return_value=mock_db_session)
        session_cm.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("core.services.webhook_service.AsyncSessionLocal", return_value=session_cm),
            patch(
                "core.services.webhook_service.create_notification", new=AsyncMock()
            ) as mock_create,
            patch("core.services.webhook_service.send_notification", new=AsyncMock()) as mock_send,
        ):
            await notify_callback_on_review_completed(
                user_id=str(uuid4()),
                profile_id=mock_callback.profile_id,
                review_id=str(uuid4()),
                callback_id=mock_callback.id,
                callback_url=mock_callback.url,
            )

            mock_create.assert_called_once()
            assert mock_create.call_args[1]["callback_id"] == mock_callback.id
            mock_send.assert_called_once()
            assert mock_send.call_args[1]["callback_url"] == mock_callback.url
            mock_db_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_callback_on_review_completed_swallows_retries_exceeded(
        self, mock_db_session: AsyncMock, mock_callback: Mock
    ) -> None:
        """Test notify_callback_on_review_completed catches RetriesExceededError and doesn't
        raise."""
        session_cm = AsyncMock()
        session_cm.__aenter__ = AsyncMock(return_value=mock_db_session)
        session_cm.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("core.services.webhook_service.AsyncSessionLocal", return_value=session_cm),
            patch("core.services.webhook_service.create_notification", new=AsyncMock()),
            patch(
                "core.services.webhook_service.send_notification",
                new=AsyncMock(side_effect=RetriesExceededError("exceeded")),
            ),
        ):
            # Should not raise.
            await notify_callback_on_review_completed(
                user_id=str(uuid4()),
                profile_id=mock_callback.profile_id,
                review_id=str(uuid4()),
                callback_id=mock_callback.id,
                callback_url=mock_callback.url,
            )

    @pytest.mark.asyncio
    async def test_notify_callback_on_review_completed_swallows_lookup_error(
        self, mock_db_session: AsyncMock, mock_callback: Mock
    ) -> None:
        """Test notify_callback_on_review_completed catches an error from create_notification's
        own DB lookup and doesn't raise."""
        mock_db_session.execute = AsyncMock(side_effect=RuntimeError("db unavailable"))

        session_cm = AsyncMock()
        session_cm.__aenter__ = AsyncMock(return_value=mock_db_session)
        session_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("core.services.webhook_service.AsyncSessionLocal", return_value=session_cm):
            # Should not raise.
            await notify_callback_on_review_completed(
                user_id=str(uuid4()),
                profile_id=str(uuid4()),
                review_id=str(uuid4()),
                callback_id=mock_callback.id,
                callback_url=mock_callback.url,
            )
