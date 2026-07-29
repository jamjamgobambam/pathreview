from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.review import ReviewCreate, ReviewResponse, ReviewListResponse
from api.schemas.share import ShareLinkResponse, PublicReviewResponse
from api.middleware.auth import get_current_user
from core.models.user import User
from core.models.review import Review
from core.database import get_db
from core.services.review_service import (
    create_review,
    create_share_link,
    get_review,
    get_share_link,
    list_reviews,
    process_review,
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


@router.get("/shared/{token}", response_model=PublicReviewResponse)
async def get_shared_review_endpoint(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PublicReviewResponse:
    """
    Public, unauthenticated read-only view of a review via a share token.
    Returns 404 if the token is unknown or malformed, 410 if it has expired.

    Declared before GET /{review_id} so that /reviews/shared/... is not
    captured by the {review_id} route.
    """
    # Reject malformed tokens up front so a non-UUID value returns 404 rather
    # than triggering a database error on the UUID column.
    try:
        UUID(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found",
        ) from None

    try:
        share_link = await get_share_link(db=db, token=token)

        if share_link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found",
            )

        # Normalize to an aware datetime so the comparison works whether the
        # backing store returns naive (SQLite) or aware (Postgres) values.
        expires_at = share_link.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Share link has expired",
            )

        return PublicReviewResponse.model_validate(share_link.review)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("get_shared_review_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shared review",
        ) from exc


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
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShareLinkResponse:
    """
    Create a public, 30-day share link for a review the current user owns.
    Returns 404 if the review does not exist or is not owned by the user.
    """
    try:
        # Reuses the ownership check: a user cannot mint a link for a review
        # that is not theirs. (user_id is stored as str; get_review annotates
        # it as UUID, so the type: ignore matches the pre-existing endpoints.)
        review = await get_review(
            db=db,
            review_id=review_id,
            user_id=current_user.id,  # type: ignore[arg-type]
        )

        if not review:
            log.warning(
                "share_link_review_not_found",
                review_id=str(review_id),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )

        share_link = await create_share_link(db=db, review_id=review_id)

        log.info(
            "share_link_created",
            review_id=str(review_id),
            user_id=str(current_user.id),
            token=str(share_link.token),
        )

        return ShareLinkResponse.model_validate(share_link)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("share_link_creation_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create share link",
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
