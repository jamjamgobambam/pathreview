"""Webhook service for managing webhook registrations and triggering events."""

from datetime import datetime
from typing import Optional
from uuid import UUID
import structlog
import httpx
import json
import hmac
import hashlib

from sqlalchemy import select, and_

from core.models.webhook import Webhook
from core.models.user import User
from api.schemas.review import ReviewResponse

log = structlog.get_logger()


def _normalize_events(events: str | list[str] | None) -> str:
    if events is None:
        return ""
    if isinstance(events, str):
        normalized = ",".join(
            event.strip() for event in events.split(",") if event.strip()
        )
        return normalized or ""
    if isinstance(events, list):
        normalized = ",".join(
            event.strip() for item in events for event in str(item).split(",") if event.strip()
        )
        return normalized or ""
    raise TypeError("events must be a string or list of strings")


async def create_webhook(
    db,
    user_id: UUID,
    url: str,
    events: str | list[str] = "review.completed",
    secret: Optional[str] = None,
    description: Optional[str] = None,
) -> Webhook:
    """
    Create a new webhook registration for a user.

    Args:
        db: Database session
        user_id: User ID
        url: Webhook callback URL
        events: Comma-separated list of events to listen for
        secret: Optional secret for HMAC signature verification
        description: Optional description of the webhook

    Returns:
        Created Webhook object
    """
    webhook = Webhook(
        user_id=user_id,
        url=url,
        events=_normalize_events(events),
        secret=secret,
        description=description,
        is_active=True,
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    log.info(
        "webhook_created",
        webhook_id=str(webhook.id),
        user_id=str(user_id),
        url=url,
        events=events,
    )

    return webhook


async def get_webhook(
    db,
    webhook_id: UUID,
    user_id: UUID,
) -> Optional[Webhook]:
    """
    Get a webhook by ID, checking that it belongs to the user.

    Args:
        db: Database session
        webhook_id: Webhook ID
        user_id: User ID

    Returns:
        Webhook object or None if not found
    """
    stmt = select(Webhook).where(
        and_(Webhook.id == webhook_id, Webhook.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_webhooks(
    db,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Webhook], int]:
    """
    List webhooks for a user with pagination.

    Args:
        db: Database session
        user_id: User ID
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Tuple of (webhooks, total_count)
    """
    offset = (page - 1) * page_size

    # Get total count
    count_stmt = select(Webhook).where(Webhook.user_id == user_id)
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    # Get paginated results
    stmt = (
        select(Webhook)
        .where(Webhook.user_id == user_id)
        .order_by(Webhook.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    webhooks = result.scalars().all()

    return webhooks, total


async def update_webhook(
    db,
    webhook_id: UUID,
    user_id: UUID,
    url: Optional[str] = None,
    events: Optional[str | list[str]] = None,
    secret: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[Webhook]:
    """
    Update a webhook.

    Args:
        db: Database session
        webhook_id: Webhook ID
        user_id: User ID
        url: New webhook URL
        events: New events list
        secret: New secret
        description: New description
        is_active: New active status

    Returns:
        Updated Webhook object or None if not found
    """
    webhook = await get_webhook(db, webhook_id, user_id)
    if not webhook:
        return None

    if url is not None:
        webhook.url = url
    if events is not None:
        webhook.events = _normalize_events(events)
    if secret is not None:
        webhook.secret = secret
    if description is not None:
        webhook.description = description
    if is_active is not None:
        webhook.is_active = is_active

    webhook.updated_at = datetime.utcnow()
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    log.info("webhook_updated", webhook_id=str(webhook_id), user_id=str(user_id))

    return webhook


async def delete_webhook(
    db,
    webhook_id: UUID,
    user_id: UUID,
) -> bool:
    """
    Delete a webhook.

    Args:
        db: Database session
        webhook_id: Webhook ID
        user_id: User ID

    Returns:
        True if deleted, False if not found
    """
    webhook = await get_webhook(db, webhook_id, user_id)
    if not webhook:
        return False

    await db.delete(webhook)
    await db.commit()

    log.info("webhook_deleted", webhook_id=str(webhook_id), user_id=str(user_id))

    return True


async def get_user_webhooks_for_event(
    db,
    user_id: UUID,
    event: str,
) -> list[Webhook]:
    """
    Get all active webhooks for a user that listen for a specific event.

    Args:
        db: Database session
        user_id: User ID
        event: Event name (e.g., "review.completed")

    Returns:
        List of Webhook objects
    """
    stmt = select(Webhook).where(
        and_(Webhook.user_id == user_id, Webhook.is_active == True)
    )
    result = await db.execute(stmt)
    webhooks = result.scalars().all()

    # Filter by event
    return [w for w in webhooks if w.has_event(event)]


def _generate_signature(payload: str, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.

    Args:
        payload: JSON payload as string
        secret: Secret key

    Returns:
        Hex digest of HMAC
    """
    return hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


async def trigger_webhook(
    webhook: Webhook,
    event: str,
    payload: dict,
    timeout: int = 10,
) -> bool:
    """
    Send a webhook event to the registered callback URL.

    Args:
        webhook: Webhook object
        event: Event name
        payload: Event payload as dictionary
        timeout: Request timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare webhook payload
        webhook_payload = {
            "event": event,
            "webhook_id": str(webhook.id),
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload,
        }

        # Serialize to JSON
        json_payload = json.dumps(webhook_payload)

        # Generate signature if secret is configured
        headers = {"Content-Type": "application/json"}
        if webhook.secret:
            signature = _generate_signature(json_payload, webhook.secret)
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        # Send webhook
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook.url,
                content=json_payload,
                headers=headers,
                timeout=timeout,
            )

            # Update webhook status
            webhook.last_triggered_at = datetime.utcnow()
            webhook.last_status_code = response.status_code

            # Check for success (2xx status codes)
            if response.status_code >= 200 and response.status_code < 300:
                webhook.failure_count = 0
                log.info(
                    "webhook_triggered_success",
                    webhook_id=str(webhook.id),
                    event=event,
                    status_code=response.status_code,
                )
                return True
            else:
                webhook.failure_count += 1
                log.warning(
                    "webhook_triggered_failed",
                    webhook_id=str(webhook.id),
                    event=event,
                    status_code=response.status_code,
                )
                return False

    except httpx.TimeoutException:
        webhook.last_triggered_at = datetime.utcnow()
        webhook.failure_count += 1
        log.warning(
            "webhook_timeout",
            webhook_id=str(webhook.id),
            event=event,
            url=webhook.url,
        )
        return False
    except Exception as exc:
        webhook.last_triggered_at = datetime.utcnow()
        webhook.failure_count += 1
        log.error(
            "webhook_trigger_error",
            webhook_id=str(webhook.id),
            event=event,
            error=str(exc),
        )
        return False


async def trigger_review_event(
    db,
    user_id: UUID,
    event: str,
    review_data: dict,
) -> None:
    """
    Trigger webhook events for all registered webhooks of a user.

    Args:
        db: Database session
        user_id: User ID
        event: Event name (e.g., "review.completed", "review.failed")
        review_data: Review data as dictionary
    """
    try:
        # Get all webhooks for this user that listen for this event
        webhooks = await get_user_webhooks_for_event(db, user_id, event)

        if not webhooks:
            log.debug(
                "no_webhooks_for_event",
                user_id=str(user_id),
                event=event,
            )
            return

        log.info(
            "triggering_webhooks",
            user_id=str(user_id),
            event=event,
            webhook_count=len(webhooks),
        )

        # Trigger all webhooks
        for webhook in webhooks:
            success = await trigger_webhook(webhook, event, review_data)
            db.add(webhook)

        # Commit all webhook status updates
        await db.commit()

        log.info(
            "webhooks_triggered",
            user_id=str(user_id),
            event=event,
            webhook_count=len(webhooks),
        )

    except Exception as exc:
        log.error(
            "trigger_review_event_error",
            user_id=str(user_id),
            event=event,
            error=str(exc),
        )
