from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_user
from api.schemas.review import (
    PublicReviewResponse,
    ReviewCreate,
    ReviewListResponse,
    ReviewResponse,
    ShareLinkResponse,
)
from core.database import get_db
from core.models.user import User
from core.services.review_service import (
    create_review,
    get_review,
    list_reviews,
    process_review,
)
from core.services.share_service import (
    ShareLinkExpiredError,
    build_share_url,
    create_share_link,
    get_review_by_share_token,
)

log = structlog.get_logger()

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse)
async def create_review_endpoint(
    data: ReviewCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Create a new review for a profile.
    Triggers ingestion pipeline and agent orchestration asynchronously.
    Returns review with status="pending" immediately.
    """
    try:
        # Create review with status="pending"
        review = await create_review(
            db=db,
            profile_id=data.profile_id,
            user_id=current_user.id,
        )

        # Add background task for processing
        background_tasks.add_task(process_review, db, review.id, data.profile_id)

        log.info(
            "review_created",
            review_id=str(review.id),
            profile_id=str(data.profile_id),
            user_id=str(current_user.id),
        )

        return ReviewResponse.model_validate(review)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("review_creation_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create review",
        )


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review_endpoint(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get a review by ID.
    Returns 404 if not found or not owned by current user.
    """
    try:
        review = await get_review(db=db, review_id=review_id, user_id=current_user.id)

        if not review:
            log.warning(
                "review_not_found",
                review_id=str(review_id),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )

        return ReviewResponse.model_validate(review)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("get_review_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve review",
        )


@router.post("/{review_id}/share", response_model=ShareLinkResponse)
async def create_share_link_endpoint(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareLinkResponse:
    """
    Create (or reuse) a public share link for a review the caller owns.
    Returns 404 if the review does not exist or is not owned by the caller
    (mirrors get_review, so it doesn't reveal whether the review exists).
    """
    try:
        share_link = await create_share_link(db=db, review_id=review_id, user_id=current_user.id)

        if share_link is None:
            log.warning(
                "share_link_review_not_found",
                review_id=str(review_id),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )

        return ShareLinkResponse(
            share_url=build_share_url(share_link.token),
            token=share_link.token,
            expires_at=share_link.expires_at,
        )

    except HTTPException:
        raise
    except Exception as exc:
        log.error("create_share_link_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create share link",
        ) from exc


@router.get("/shared/{token}", response_model=PublicReviewResponse)
async def get_shared_review_endpoint(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> PublicReviewResponse:
    """
    Public, read-only view of a review via its share token. No authentication.
    Returns 404 for an unknown/invalid token and 410 Gone for an expired one.
    """
    try:
        review = await get_review_by_share_token(db=db, token=token)

        if review is None:
            # Unknown token, or the review was deleted (FK cascade removed the link).
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared review not found",
            )

        return PublicReviewResponse.model_validate(review)

    except ShareLinkExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This share link has expired",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        log.error("get_shared_review_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shared review",
        ) from exc


@router.get("", response_model=ReviewListResponse)
async def list_reviews_endpoint(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    List reviews for current user with pagination.
    """
    try:
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20

        reviews, total = await list_reviews(
            db=db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
        )

        return ReviewListResponse(
            items=[ReviewResponse.model_validate(r) for r in reviews],
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as exc:
        log.error("list_reviews_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list reviews",
        )


@router.get("/{review_id}/status")
async def get_review_status(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get review status and progress.
    Returns {review_id, status, progress_pct}
    """
    try:
        review = await get_review(db=db, review_id=review_id, user_id=current_user.id)

        if not review:
            log.warning(
                "review_not_found",
                review_id=str(review_id),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )

        return {
            "review_id": str(review.id),
            "status": review.status,
            "progress_pct": getattr(review, "progress_pct", 0),
        }

    except HTTPException:
        raise
    except Exception as exc:
        log.error("get_review_status_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve review status",
        )
