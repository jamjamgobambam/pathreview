from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_user
from api.schemas.review import SharedReviewResponse, ShareLinkResponse
from core.database import get_db
from core.models.user import User
from core.services.share_service import (
    ReviewNotFoundError,
    ReviewNotShareableError,
    create_share_link,
    get_shared_review,
)

log = structlog.get_logger()

router = APIRouter(tags=["share"])


@router.post(
    "/reviews/{review_id}/share",
    response_model=ShareLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_share_link_endpoint(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareLinkResponse:
    """
    Create a public, expiring share link for a completed review.

    Reuses an existing unexpired link if one exists. Returns 404 if the review is
    not found or not owned by the user, 409 if the review is not complete.
    """
    try:
        share_link = await create_share_link(db=db, review_id=review_id, user_id=current_user.id)
    except ReviewNotFoundError as exc:
        log.warning(
            "share_link_review_not_found",
            review_id=str(review_id),
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        ) from exc
    except ReviewNotShareableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only completed reviews can be shared",
        ) from exc

    return ShareLinkResponse.model_validate(share_link)


@router.get("/share/{token}", response_model=SharedReviewResponse)
async def get_shared_review_endpoint(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> SharedReviewResponse:
    """
    Public, unauthenticated read of a shared review summary.

    Deliberately requires no authentication: anyone with the token can view the
    summary. Returns 404 if the token is unknown or the link has expired.
    """
    share_link = await get_shared_review(db=db, token=token)

    if share_link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found or expired",
        )

    review = share_link.review
    return SharedReviewResponse.model_validate(
        {
            "overall_score": review.overall_score,
            "sections": review.sections,
            "created_at": review.created_at,
            "expires_at": share_link.expires_at,
        }
    )
