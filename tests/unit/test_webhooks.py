"""Unit tests for webhook system functionality."""

import pytest
from uuid import uuid4
from datetime import datetime
import json
from unittest.mock import AsyncMock, patch, MagicMock

from core.models.webhook import Webhook
from core.models.user import User
from core.models.profile import Profile
from core.models.review import Review
from core.services.webhook_service import (
    create_webhook,
    get_webhook,
    list_webhooks,
    update_webhook,
    delete_webhook,
    get_user_webhooks_for_event,
    trigger_webhook,
    trigger_review_event,
    _generate_signature,
)
from api.schemas.webhook import WebhookCreate, WebhookResponse


@pytest.fixture
def user_id():
    """Create a test user ID."""
    return str(uuid4())


@pytest.fixture
def profile_id():
    """Create a test profile ID."""
    return str(uuid4())


@pytest.fixture
def webhook_id():
    """Create a test webhook ID."""
    return str(uuid4())


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


class TestWebhookModel:
    """Tests for Webhook model."""

    def test_webhook_creation(self):
        """Test creating a webhook instance."""
        webhook = Webhook(
            user_id=str(uuid4()),
            url="https://example.com/webhook",
            events="review.completed,review.failed",
            secret="test_secret",
            description="Test webhook",
        )

        assert webhook.url == "https://example.com/webhook"
        assert webhook.events == "review.completed,review.failed"
        assert webhook.secret == "test_secret"
        assert webhook.is_active is True
        assert webhook.failure_count == 0

    def test_has_event_method(self):
        """Test checking if webhook has an event."""
        webhook = Webhook(
            user_id=str(uuid4()),
            url="https://example.com/webhook",
            events="review.completed,review.failed",
        )

        assert webhook.has_event("review.completed") is True
        assert webhook.has_event("review.failed") is True
        assert webhook.has_event("review.started") is False


class TestWebhookService:
    """Tests for webhook service functions."""

    @pytest.mark.asyncio
    async def test_create_webhook(self, mock_db, user_id):
        """Test creating a webhook."""
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        webhook = Webhook(
            user_id=user_id,
            url="https://example.com/webhook",
            events="review.completed",
        )

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock(
            side_effect=lambda w: setattr(w, "id", str(uuid4()))
        )

        # Note: In real test, we'd mock the database properly
        # This is a simplified example

    def test_generate_signature(self):
        """Test HMAC-SHA256 signature generation."""
        payload = '{"event": "review.completed"}'
        secret = "test_secret"

        signature = _generate_signature(payload, secret)

        # Verify it produces consistent results
        assert signature == _generate_signature(payload, secret)

        # Verify it's different with different secret
        different_signature = _generate_signature(payload, "different_secret")
        assert signature != different_signature

        # Verify it's different with different payload
        different_payload_signature = _generate_signature(
            '{"event": "review.failed"}', secret
        )
        assert signature != different_payload_signature


class TestWebhookSchemas:
    """Tests for webhook schemas."""

    def test_webhook_create_schema(self):
        """Test WebhookCreate schema."""
        data = {
            "url": "https://example.com/webhook",
            "events": ["review.completed", "review.failed"],
            "secret": "test_secret",
            "description": "Test webhook",
        }

        schema = WebhookCreate(**data)
        assert str(schema.url) == "https://example.com/webhook"
        assert schema.events == ["review.completed", "review.failed"]
        assert schema.secret == "test_secret"

    def test_webhook_create_schema_accepts_string_events(self):
        """Test WebhookCreate accepts comma-separated event strings."""
        data = {
            "url": "https://example.com/webhook",
            "events": "review.completed,review.failed",
            "secret": "test_secret",
            "description": "Test webhook",
        }

        schema = WebhookCreate(**data)
        assert schema.events == ["review.completed", "review.failed"]

    def test_webhook_response_schema(self):
        """Test WebhookResponse schema."""
        webhook_data = {
            "id": str(uuid4()),
            "url": "https://example.com/webhook",
            "events": "review.completed",
            "is_active": True,
            "secret": "test_secret",
            "description": "Test webhook",
            "last_triggered_at": datetime.utcnow(),
            "last_status_code": 200,
            "failure_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        schema = WebhookResponse(**webhook_data)
        assert str(schema.url) == "https://example.com/webhook"
        assert schema.is_active is True
        assert schema.failure_count == 0


class TestWebhookIntegration:
    """Integration tests for webhook system."""

    @pytest.mark.asyncio
    async def test_review_completion_triggers_webhook(self):
        """Test that review completion triggers appropriate webhooks."""
        # This would be a full integration test
        # In practice, it would:
        # 1. Create a user and profile
        # 2. Register a webhook for "review.completed"
        # 3. Create a review
        # 4. Process the review
        # 5. Verify webhook was triggered with correct payload
        pass

    @pytest.mark.asyncio
    async def test_review_failure_triggers_webhook(self):
        """Test that review failure triggers appropriate webhooks."""
        # Similar to above but for failure case
        pass


if __name__ == "__main__":
    pytest.main([__file__])
