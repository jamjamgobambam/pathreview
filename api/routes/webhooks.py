"""API routes for webhook management."""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
import structlog

from api.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookListResponse,
)
from api.middleware.auth import get_current_user
from core.models.user import User
from core.database import get_db
from core.services.webhook_service import (
    create_webhook,
    get_webhook,
    list_webhooks,
    update_webhook,
    delete_webhook,
)

log = structlog.get_logger()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def register_webhook(
    data: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Register a new webhook for the current user.

    The webhook will receive a POST request with the event payload whenever
    one of the registered events occurs.

    Required fields:
    - url: The callback URL where events will be sent
    - events: Comma-separated list of events to listen for (default: "review.completed")
    - secret: Optional secret for HMAC-SHA256 signature verification

    Available events:
    - review.completed: Triggered when a portfolio review completes successfully
    - review.failed: Triggered when a portfolio review fails

    Returns:
        Created webhook with ID and configuration
    """
    try:
        webhook = await create_webhook(
            db=db,
            user_id=current_user.id,
            url=data.url,
            events=data.events,
            secret=data.secret,
            description=data.description,
        )

        log.info(
            "webhook_registered",
            webhook_id=str(webhook.id),
            user_id=str(current_user.id),
            url=data.url,
        )

        return WebhookResponse.model_validate(webhook)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("webhook_registration_error", user_id=str(current_user.id), error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register webhook",
        )


@router.get("", response_model=WebhookListResponse)
async def list_user_webhooks(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    List all webhooks for the current user.

    Supports pagination with optional page and page_size parameters.

    Returns:
        List of webhooks with pagination metadata
    """
    try:
        webhooks, total = await list_webhooks(
            db=db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
        )

        return WebhookListResponse(
            items=[WebhookResponse.model_validate(w) for w in webhooks],
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as exc:
        log.error("list_webhooks_error", user_id=str(current_user.id), error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list webhooks",
        )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_user_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get a specific webhook by ID.

    Returns:
        Webhook details or 404 if not found or not owned by current user
    """
    try:
        webhook = await get_webhook(db=db, webhook_id=webhook_id, user_id=current_user.id)

        if not webhook:
            log.warning(
                "webhook_not_found",
                webhook_id=str(webhook_id),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found",
            )

        return WebhookResponse.model_validate(webhook)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("get_webhook_error", webhook_id=str(webhook_id), error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve webhook",
        )


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_user_webhook(
    webhook_id: UUID,
    data: WebhookUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Update a webhook configuration.

    All fields are optional. Only provided fields will be updated.

    Returns:
        Updated webhook details or 404 if not found
    """
    try:
        webhook = await update_webhook(
            db=db,
            webhook_id=webhook_id,
            user_id=current_user.id,
            url=data.url,
            events=data.events,
            secret=data.secret,
            description=data.description,
            is_active=data.is_active,
        )

        if not webhook:
            log.warning(
                "webhook_not_found_for_update",
                webhook_id=str(webhook_id),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found",
            )

        log.info(
            "webhook_updated",
            webhook_id=str(webhook_id),
            user_id=str(current_user.id),
        )

        return WebhookResponse.model_validate(webhook)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("webhook_update_error", webhook_id=str(webhook_id), error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update webhook",
        )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Delete a webhook.

    Returns:
        204 No Content on success or 404 if not found
    """
    try:
        deleted = await delete_webhook(db=db, webhook_id=webhook_id, user_id=current_user.id)

        if not deleted:
            log.warning(
                "webhook_not_found_for_deletion",
                webhook_id=str(webhook_id),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found",
            )

        log.info(
            "webhook_deleted",
            webhook_id=str(webhook_id),
            user_id=str(current_user.id),
        )

    except HTTPException:
        raise
    except Exception as exc:
        log.error("webhook_deletion_error", webhook_id=str(webhook_id), error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete webhook",
        )
