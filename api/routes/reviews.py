"""API routes for creating, retrieving, listing, and sharing reviews."""

from typing import Annotated
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
    ReviewShareResponse,
)
from core.database import get_db
from core.models.user import User
from core.services.review_service import (
    create_review,
    create_share_link,
    get_public_review,
    get_review,
    list_reviews,
    process_review,
)

log = structlog.get_logger()

router = APIRouter(prefix="/reviews", tags=["reviews"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=ReviewResponse)
async def create_review_endpoint(
    data: ReviewCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> ReviewResponse:
    """
    Create a new review for a profile.

    Triggers ingestion pipeline and agent orchestration asynchronously.
    Returns the review with status="pending" immediately.
    """
    try:
        review = await create_review(
            db=db,
            profile_id=data.profile_id,
            user_id=current_user.id,
        )

        background_tasks.add_task(
            process_review,
            db,
            review.id,
            data.profile_id,
        )

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
        log.error(
            "review_creation_error",
            error=str(exc),
        )
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create review",
        ) from exc


@router.get("", response_model=ReviewListResponse)
async def list_reviews_endpoint(
    current_user: CurrentUser,
    db: DatabaseSession,
    page: int = 1,
    page_size: int = 20,
) -> ReviewListResponse:
    """
    List reviews belonging to the current user.

    Results are paginated using the requested page and page size.
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
            items=[ReviewResponse.model_validate(review) for review in reviews],
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as exc:
        log.error(
            "list_reviews_error",
            user_id=str(current_user.id),
            error=str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list reviews",
        ) from exc


@router.get(
    "/public/{share_token}",
    response_model=PublicReviewResponse,
)
async def get_public_review_endpoint(
    share_token: str,
    db: DatabaseSession,
) -> PublicReviewResponse:
    """
    Retrieve a shared review without authentication.

    The share token must belong to a completed review and must not
    be expired.
    """
    try:
        review = await get_public_review(
            db=db,
            share_token=share_token,
        )

        if not review:
            log.warning(
                "public_review_not_found",
                share_token=share_token,
            )

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared review not found or link expired",
            )

        return PublicReviewResponse.model_validate(review)

    except HTTPException:
        raise

    except Exception as exc:
        log.error(
            "public_review_retrieval_error",
            error=str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shared review",
        ) from exc


@router.post(
    "/{review_id}/share",
    response_model=ReviewShareResponse,
)
async def create_review_share_link(
    review_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> ReviewShareResponse:
    """
    Generate a public share link for a completed review.

    The review must belong to the authenticated user and have
    status="complete". The generated link expires after 30 days.
    """
    try:
        review = await create_share_link(
            db=db,
            review_id=review_id,
            user_id=current_user.id,
        )

        if not review:
            log.warning(
                "review_not_found_for_sharing",
                review_id=str(review_id),
                user_id=str(current_user.id),
            )

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )

        if not review.share_token or not review.share_expires_at:
            log.error(
                "review_share_link_missing_fields",
                review_id=str(review_id),
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create share link",
            )

        log.info(
            "review_share_link_returned",
            review_id=str(review.id),
            user_id=str(current_user.id),
            expires_at=review.share_expires_at.isoformat(),
        )

        return ReviewShareResponse(
            share_token=review.share_token,
            share_url=f"/shared-reviews/{review.share_token}",
            expires_at=review.share_expires_at,
        )

    except ValueError as exc:
        log.warning(
            "review_not_shareable",
            review_id=str(review_id),
            user_id=str(current_user.id),
            error=str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        log.error(
            "review_share_link_creation_error",
            review_id=str(review_id),
            user_id=str(current_user.id),
            error=str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create share link",
        ) from exc


@router.get("/{review_id}/status")
async def get_review_status(
    review_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> dict[str, str | int]:
    """
    Get review processing status and progress.

    Returns the review ID, current status, and progress percentage.
    """
    try:
        review = await get_review(
            db=db,
            review_id=review_id,
            user_id=current_user.id,
        )

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
        log.error(
            "get_review_status_error",
            review_id=str(review_id),
            error=str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve review status",
        ) from exc


@router.get(
    "/{review_id}",
    response_model=ReviewResponse,
)
async def get_review_endpoint(
    review_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> ReviewResponse:
    """
    Get a review by ID.

    Returns 404 if the review does not exist or does not belong
    to the current user.
    """
    try:
        review = await get_review(
            db=db,
            review_id=review_id,
            user_id=current_user.id,
        )

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
        log.error(
            "get_review_error",
            review_id=str(review_id),
            error=str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve review",
        ) from exc
