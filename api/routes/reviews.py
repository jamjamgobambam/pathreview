from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_user
from api.schemas.review import (
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
    get_shared_review,
    list_reviews,
    process_review,
    share_review,
)

log = structlog.get_logger()

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse)
async def create_review_endpoint(
    data: ReviewCreate,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewResponse:
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
            user_id=UUID(current_user.id),
        )

        # Add background task for processing
        background_tasks.add_task(process_review, db, UUID(review.id), data.profile_id)

        log.info(
            "review_created",
            review_id=str(review.id),
            profile_id=str(data.profile_id),
            user_id=str(current_user.id),
        )

        response: ReviewResponse = ReviewResponse.model_validate(review)
        return response

    except HTTPException:
        raise
    except Exception as exc:
        log.error("review_creation_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create review",
        ) from exc


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review_endpoint(
    review_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewResponse:
    """
    Get a review by ID.
    Returns 404 if not found or not owned by current user.
    """
    try:
        review = await get_review(db=db, review_id=review_id, user_id=UUID(current_user.id))

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

        response: ReviewResponse = ReviewResponse.model_validate(review)
        return response

    except HTTPException:
        raise
    except Exception as exc:
        log.error("get_review_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve review",
        ) from exc


@router.get("", response_model=ReviewListResponse)
async def list_reviews_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
) -> ReviewListResponse:
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
            user_id=UUID(current_user.id),
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
        ) from exc


@router.post("/{review_id}/share", response_model=ShareLinkResponse)
async def share_review_endpoint(
    review_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShareLinkResponse:
    """
    Enable public sharing for a review owned by the current user.
    Idempotent: if a valid share link already exists, it is returned
    unchanged instead of being regenerated.
    """
    try:
        review = await share_review(db=db, review_id=review_id, user_id=UUID(current_user.id))

        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )

        # share_review always sets share_expires_at when it returns a review
        assert review.share_expires_at is not None

        return ShareLinkResponse(
            review_id=UUID(review.id),
            is_public=review.is_public,
            share_url=f"/shared/{review.id}",
            expires_at=review.share_expires_at,
        )

    except HTTPException:
        raise
    except Exception as exc:
        log.error("share_review_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to share review",
        ) from exc


@router.get("/{review_id}/shared", response_model=ReviewResponse)
async def get_shared_review_endpoint(
    review_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewResponse:
    """
    Get a publicly shared review by ID. No authentication required.
    Returns 404 if the review doesn't exist, isn't public, or its share
    link has expired.
    """
    try:
        review = await get_shared_review(db=db, review_id=review_id)

        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared review not found or expired",
            )

        response: ReviewResponse = ReviewResponse.model_validate(review)
        return response

    except HTTPException:
        raise
    except Exception as exc:
        log.error("get_shared_review_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shared review",
        ) from exc


@router.get("/{review_id}/status")
async def get_review_status(
    review_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str | int]:
    """
    Get review status and progress.
    Returns {review_id, status, progress_pct}
    """
    try:
        review = await get_review(db=db, review_id=review_id, user_id=UUID(current_user.id))

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
        ) from exc
