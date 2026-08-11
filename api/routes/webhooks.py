from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_user
from api.schemas.webhook import CallbackCreate, CallbackResponse
from core.database import get_db
from core.models.user import User
from core.services.webhook_service import (
    CallbackAlreadyExistsError,
    ProfileNotFoundError,
    delete_callback_url,
    set_callback_url,
)

log = structlog.get_logger()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/callbacks", response_model=CallbackResponse)
async def register_callback_endpoint(
    data: CallbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CallbackResponse:
    """
    Register a callback URL for a profile. Only one callback is allowed per profile;
    delete the existing one first to change it.
    """
    try:
        callback = await set_callback_url(
            db=db,
            user_id=UUID(current_user.id),
            profile_id=data.profile_id,
            url=str(data.url),
        )

        log.info(
            "callback_registered",
            callback_id=str(callback.id),
            profile_id=str(data.profile_id),
            user_id=str(current_user.id),
        )

        return CallbackResponse.model_validate(callback)

    except ProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        ) from exc
    except CallbackAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A callback is already registered for this profile. Delete it first.",
        ) from exc
    except Exception as exc:
        log.error("callback_registration_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register callback",
        ) from exc


@router.delete("/callbacks/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_callback_endpoint(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete the callback registered for a profile by the current user.
    """
    try:
        deleted = await delete_callback_url(
            db=db,
            user_id=UUID(current_user.id),
            profile_id=profile_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Callback not found",
            )

        log.info(
            "callback_deleted",
            profile_id=str(profile_id),
            user_id=str(current_user.id),
        )
        return None

    except HTTPException as exc:
        log.warning("callback_deletion_http_error", status_code=exc.status_code, detail=exc.detail)
        raise
    except Exception as exc:
        log.error("callback_deletion_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete callback",
        ) from exc
