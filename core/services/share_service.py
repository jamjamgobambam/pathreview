"""Service for creating and retrieving public share links for reviews."""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.profile import Profile
from core.models.review import Review

log = structlog.get_logger()

_SHARE_LINK_TTL_DAYS = 30


async def create_share_link(db: AsyncSession, review_id: UUID, user_id: UUID) -> Review:
    """Return the Review with an active share token, creating one if needed.

    Raises ValueError if the review is not found or not owned by user_id.
    """
    stmt = (
        select(Review)
        .join(Profile)
        .where(and_(Review.id == str(review_id), Profile.user_id == str(user_id)))
    )
    result = await db.execute(stmt)
    review: Review | None = result.scalars().first()

    if review is None:
        log.warning("share_link_not_found", review_id=str(review_id), user_id=str(user_id))
        raise ValueError("Review not found or not owned by user")

    now = datetime.now(UTC)
    if (
        review.share_token is not None
        and review.share_token_expires_at is not None
        and review.share_token_expires_at > now
    ):
        log.info("share_link_reused", review_id=str(review_id))
        return review

    review.share_token = secrets.token_urlsafe(16)
    review.share_token_expires_at = now + timedelta(days=_SHARE_LINK_TTL_DAYS)
    await db.commit()
    log.info("share_link_created", review_id=str(review_id))
    return review


async def get_public_review(db: AsyncSession, token: str) -> Review:
    """Return the Review for a valid, non-expired share token.

    Raises LookupError if the token is not found.
    Raises ValueError if the token has expired.
    """
    stmt = select(Review).where(Review.share_token == token)
    result = await db.execute(stmt)
    review: Review | None = result.scalars().first()

    if review is None:
        log.warning("share_link_token_not_found", token=token)
        raise LookupError("No review found for the given token")

    now = datetime.now(UTC)
    if review.share_token_expires_at is None or review.share_token_expires_at <= now:
        log.warning("share_link_expired", token=token)
        raise ValueError("Share link has expired")

    return review
