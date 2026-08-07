from typing import Any, cast
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_user
from api.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse, ShareLinkResponse
from core.database import get_db
from core.models.user import User
from core.services.review_service import (
    create_review,
    get_review,
    list_reviews,
    process_review,
)
from core.services.share_service import create_share_link

log = structlog.get_logger()

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse)
async def create_review_endpoint(
    data: ReviewCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
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
            user_id=current_user.id,  # type: ignore[arg-type]
        )

        # Add background task for processing
        background_tasks.add_task(process_review, db, review.id, data.profile_id)  # type: ignore[arg-type]

        log.info(
            "review_created",
            review_id=str(review.id),
            profile_id=str(data.profile_id),
            user_id=str(current_user.id),
        )

        return cast("ReviewResponse", ReviewResponse.model_validate(review))

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
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ReviewResponse:
    """
    Get a review by ID.
    Returns 404 if not found or not owned by current user.
    """
    try:
        review = await get_review(db=db, review_id=review_id, user_id=current_user.id)  # type: ignore[arg-type]

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

        return cast("ReviewResponse", ReviewResponse.model_validate(review))

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
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
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
            user_id=current_user.id,  # type: ignore[arg-type]
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


@router.post("/{review_id}/share-link", response_model=ShareLinkResponse)
async def create_share_link_endpoint(
    review_id: UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ShareLinkResponse:
    """
    Create or return an existing shareable link for a review.
    Returns a token and expiry date. The public URL is constructed client-side.
    Returns 404 if the review is not found or not owned by the current user.
    """
    try:
        review = await create_share_link(
            db=db,
            review_id=review_id,
            user_id=UUID(current_user.id),
        )
        assert review.share_token is not None
        assert review.share_token_expires_at is not None
        return ShareLinkResponse(
            token=review.share_token,
            expires_at=review.share_token_expires_at,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        ) from None
    except Exception as exc:
        log.error("create_share_link_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create share link",
        ) from exc


@router.get("/{review_id}/status")
async def get_review_status(
    review_id: UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Get review status and progress.
    Returns {review_id, status, progress_pct}
    """
    try:
        review = await get_review(db=db, review_id=review_id, user_id=current_user.id)  # type: ignore[arg-type]

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
