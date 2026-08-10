"""Tests for webhook_service.py"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.services.webhook_service import (
    delete_webhook,
    deliver_webhook_notification,
    list_webhooks,
    register_webhook,
)


@pytest.mark.unit
class TestWebhookService:
    """Test suite for webhook_service module."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_register_webhook_creates_active_webhook(self, mock_db_session):
        """Registering a webhook should create an active registration."""
        user_id = uuid4()

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "core.services.webhook_service.secrets.token_urlsafe", return_value="generated-secret"
        ):
            webhook, secret = await register_webhook(
                mock_db_session,
                user_id,
                "https://example.com/callback",
            )

            assert webhook.url == "https://example.com/callback"
            assert secret == "generated-secret"
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_webhooks_returns_user_webhooks(self, mock_db_session):
        """Listing should return only the current user's active registrations."""
        user_id = uuid4()
        webhook = Mock(id=uuid4(), url="https://example.com/callback", is_active=True)

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [webhook]
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        webhooks = await list_webhooks(mock_db_session, user_id)

        assert webhooks == [webhook]

    @pytest.mark.asyncio
    async def test_delete_webhook_marks_registration_inactive(self, mock_db_session):
        """Deleting should mark the record inactive for the current user."""
        user_id = uuid4()
        webhook = Mock(id=uuid4(), user_id=user_id, is_active=True)

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = webhook
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        deleted = await delete_webhook(mock_db_session, webhook.id, user_id)

        assert deleted is True
        assert webhook.is_active is False
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_deliver_webhook_notification_records_success(self, mock_db_session):
        """Successful delivery should create a success delivery row."""
        review_id = uuid4()
        review = Mock(
            id=review_id,
            profile_id=uuid4(),
            status="complete",
            sections=[{"section_name": "summary", "content": "ok"}],
            overall_score=0.9,
            error_message=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        profile = Mock(id=review.profile_id, user_id=uuid4())
        webhook = Mock(
            id=uuid4(), url="https://example.com/callback", secret="secret", is_active=True
        )

        review_result = Mock()
        review_result.scalars.return_value.first.return_value = review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = profile
        webhook_result = Mock()
        webhook_result.scalars.return_value.all.return_value = [webhook]

        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result, webhook_result]
        )

        with patch(
            "core.services.webhook_service._send_with_retry", new=AsyncMock(return_value=200)
        ):
            await deliver_webhook_notification(mock_db_session, review_id)

        assert mock_db_session.add.call_count >= 2

    @pytest.mark.asyncio
    async def test_deliver_webhook_notification_retries_then_succeeds(self, mock_db_session):
        """Webhook delivery should retry transient failures before succeeding."""
        review_id = uuid4()
        review = Mock(
            id=review_id,
            profile_id=uuid4(),
            status="complete",
            sections=[],
            overall_score=0.8,
            error_message=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        profile = Mock(id=review.profile_id, user_id=uuid4())
        webhook = Mock(
            id=uuid4(), url="https://example.com/callback", secret="secret", is_active=True
        )

        review_result = Mock()
        review_result.scalars.return_value.first.return_value = review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = profile
        webhook_result = Mock()
        webhook_result.scalars.return_value.all.return_value = [webhook]

        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result, webhook_result]
        )

        with patch(
            "core.services.webhook_service._send_with_retry",
            new=AsyncMock(side_effect=[RuntimeError("temporary"), 200]),
        ) as send_mock:
            await deliver_webhook_notification(mock_db_session, review_id)

        assert send_mock.await_count == 2

    @pytest.mark.asyncio
    async def test_deliver_webhook_notification_logs_failed_delivery_after_retries(
        self, mock_db_session
    ):
        """Exhausted retries should leave a failed delivery record rather than crashing."""
        review_id = uuid4()
        review = Mock(
            id=review_id,
            profile_id=uuid4(),
            status="failed",
            sections=None,
            overall_score=None,
            error_message="boom",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        profile = Mock(id=review.profile_id, user_id=uuid4())
        webhook = Mock(
            id=uuid4(), url="https://example.com/callback", secret="secret", is_active=True
        )

        review_result = Mock()
        review_result.scalars.return_value.first.return_value = review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = profile
        webhook_result = Mock()
        webhook_result.scalars.return_value.all.return_value = [webhook]

        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result, webhook_result]
        )

        with patch(
            "core.services.webhook_service._send_with_retry",
            new=AsyncMock(side_effect=RuntimeError("persistent failure")),
        ):
            await deliver_webhook_notification(mock_db_session, review_id)

        assert mock_db_session.add.call_count >= 2
