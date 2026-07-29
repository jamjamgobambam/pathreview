from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from api.middleware.auth import get_current_user
from api.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse
from core.database import get_db
from core.models.user import User
from core.services.review_service import (
    get_or_create_review,
    get_review,
    list_reviews,
    process_review,
)

log = structlog.get_logger()

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse)
async def create_review_endpoint(
    data: ReviewCreate,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_db)],
) -> ReviewResponse:
    """
    Get or create a review for a profile.
    If portfolio hasn't changed, returns cached review.
    Otherwise, creates new review and triggers pipeline asynchronously.
    """
    try:
        # Get or create review (checks cache based on content hash)
        review = await get_or_create_review(
            db=db,
            profile_id=data.profile_id,
            user_id=current_user.id,
        )

        # Only queue background task if review is pending (not cached)
        if review.status == "pending":
            background_tasks.add_task(process_review, db, review.id, data.profile_id)
            log.info(
                "review_created",
                review_id=str(review.id),
                profile_id=str(data.profile_id),
                user_id=str(current_user.id),
            )
        else:
            log.info(
                "review_returned_from_cache",
                review_id=str(review.id),
                profile_id=str(data.profile_id),
            )

        return ReviewResponse.model_validate(review)  # type: ignore

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
    db: Annotated[Any, Depends(get_db)],
) -> ReviewResponse:
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

        return ReviewResponse.model_validate(review)  # type: ignore

    except HTTPException:
        raise
    except Exception as exc:
        log.error("get_review_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve review",
        ) from exc  # noqa: B904


@router.get("", response_model=ReviewListResponse)
async def list_reviews_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_db)],
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
        ) from exc  # noqa: B904


@router.get("/{review_id}/status")
async def get_review_status(
    review_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_db)],
) -> dict[str, Any]:
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
        ) from exc  # noqa: B904
