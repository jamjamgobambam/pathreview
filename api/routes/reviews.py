from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.middleware.auth import get_current_user
from api.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse
from api.schemas.share import PublicReviewResponse, ShareTokenResponse
from core.database import get_db
from core.models.share_token import ShareToken
from core.models.user import User
from core.services.review_service import (
    create_review,
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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

        return ReviewResponse.model_validate(review)  # type: ignore[no-any-return]

    except HTTPException:
        raise
    except Exception as exc:
        log.error("review_creation_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create review",
        )


@router.get("/public/{token}", response_model=PublicReviewResponse)
async def get_public_review(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> PublicReviewResponse:
    """
    Return read-only review data for a valid, unexpired share token.

    Returns 404 for unknown tokens.
    Returns 410 Gone for expired tokens.
    Returns 400 if the linked review is not complete.
    """
    stmt = (
        select(ShareToken).where(ShareToken.token == token).options(joinedload(ShareToken.review))
    )
    result = await db.execute(stmt)
    share_token = result.scalars().first()

    if share_token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found",
        )

    now = datetime.now(UTC)
    expires_at = share_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Token has expired",
        )

    review = share_token.review
    if review.status != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review is not complete",
        )

    return PublicReviewResponse.model_validate(review)  # type: ignore[no-any-return]


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review_endpoint(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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

        return ReviewResponse.model_validate(review)  # type: ignore[no-any-return]

    except HTTPException:
        raise
    except Exception as exc:
        log.error("get_review_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve review",
        )


@router.get("", response_model=ReviewListResponse)
async def list_reviews_endpoint(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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
        )


@router.get("/{review_id}/status")
async def get_review_status(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
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
        )


@router.post("/{review_id}/share", response_model=ShareTokenResponse)
async def create_share_token(
    review_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareTokenResponse:
    """
    Generate (or return existing active) share token for a review.

    If an unexpired token already exists for this review, it is returned.
    Otherwise a new 30-day token is generated and persisted.
    Returns 404 if review not found or not owned by current user.
    Returns 400 if review is not yet complete.
    """
    try:
        review = await get_review(db=db, review_id=review_id, user_id=UUID(current_user.id))

        if review is None:
            log.warning(
                "share_token_review_not_found",
                review_id=str(review_id),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )

        if review.status != "complete":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review is not yet complete",
            )

        # Return existing active token if one exists
        now = datetime.now(UTC)
        stmt = select(ShareToken).where(
            ShareToken.review_id == str(review_id),
            ShareToken.expires_at > now,
        )
        result = await db.execute(stmt)
        share_token = result.scalars().first()

        if share_token is None:
            share_token = ShareToken(
                review_id=str(review_id),
                expires_at=now + timedelta(days=30),
            )
            db.add(share_token)
            await db.commit()
            await db.refresh(share_token)

        base_url = str(request.base_url).rstrip("/")
        share_url = f"{base_url}/share/{share_token.token}"

        log.info(
            "share_token_created",
            review_id=str(review_id),
            token=share_token.token,
        )

        return ShareTokenResponse(
            token=share_token.token,
            share_url=share_url,
            expires_at=share_token.expires_at,
        )

    except HTTPException:
        raise
    except Exception as exc:
        log.error("create_share_token_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create share token",
        )
