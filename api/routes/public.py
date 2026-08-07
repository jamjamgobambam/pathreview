from typing import cast

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.review import PublicReviewResponse
from core.database import get_db
from core.services.share_service import get_public_review

log = structlog.get_logger()

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/reviews/{token}", response_model=PublicReviewResponse)
async def get_public_review_endpoint(
    token: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PublicReviewResponse:
    """
    Retrieve a read-only review summary by share token. No authentication required.
    Returns 404 if the token does not exist.
    Returns 410 if the token has expired.
    """
    try:
        review = await get_public_review(db=db, token=token)
        return cast("PublicReviewResponse", PublicReviewResponse.model_validate(review))
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        ) from None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired",
        ) from None
    except Exception as exc:
        log.error("get_public_review_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve review",
        ) from exc
