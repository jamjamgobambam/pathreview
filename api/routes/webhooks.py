from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_user
from api.schemas.webhook import WebhookCreate, WebhookResponse
from core.database import get_db
from core.models.user import User
from core.services.webhook_service import (
    delete_webhook,
    list_webhooks,
    register_webhook,
)

log = structlog.get_logger()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookResponse)
async def create_webhook_endpoint(
    data: WebhookCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookResponse:
    """Register a webhook callback for the current user."""
    try:
        webhook, secret = await register_webhook(db, current_user.id, str(data.url))
        response = WebhookResponse.model_validate({**webhook.__dict__, "secret": secret})
        return response
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        log.error("webhook_registration_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register webhook",
        ) from exc


@router.get("", response_model=list[WebhookResponse])
async def list_webhook_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[WebhookResponse]:
    """List active webhooks registered by the current user."""
    try:
        webhooks = await list_webhooks(db, current_user.id)
        return [WebhookResponse.model_validate(webhook) for webhook in webhooks]
    except Exception as exc:
        log.error("webhook_list_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list webhooks",
        ) from exc


@router.delete("/{webhook_id}")
async def delete_webhook_endpoint(
    webhook_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Deactivate a webhook registration for the current user."""
    try:
        deleted = await delete_webhook(db, webhook_id, current_user.id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
        return {"message": "Webhook deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        log.error("webhook_delete_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete webhook",
        ) from exc
