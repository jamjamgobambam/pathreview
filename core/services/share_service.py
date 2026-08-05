"""Service functions for creating and resolving public review share links."""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models.profile import Profile
from core.models.review import Review
from core.models.share_link import ShareLink

log = structlog.get_logger()

# Number of random bytes for a share token. token_urlsafe(32) yields a ~43
# character URL-safe string, comfortably within the token column's length.
SHARE_TOKEN_BYTES = 32

# How long a share link stays valid after creation.
SHARE_LINK_EXPIRE_DAYS = 30


class ShareLinkError(Exception):
    """Base class for share-link creation errors."""


class ReviewNotFoundError(ShareLinkError):
    """Raised when the review does not exist or is not owned by the user."""


class ReviewNotShareableError(ShareLinkError):
    """Raised when the review exists but is not in a shareable (complete) state."""


async def create_share_link(db: AsyncSession, review_id: UUID, user_id: str) -> ShareLink:
    """Create (or reuse) a public share link for a completed review.

    The caller must own the review. If an unexpired link already exists for the
    review it is reused, so repeated clicks yield a stable URL rather than a new
    token each time.

    Args:
        db: Async database session.
        review_id: ID of the review to share.
        user_id: ID of the authenticated user requesting the link.

    Returns:
        The existing or newly created ShareLink.

    Raises:
        ReviewNotFoundError: If the review does not exist or is not owned by the user.
        ReviewNotShareableError: If the review is not complete.
    """
    # Verify the review exists and belongs to the requesting user.
    stmt = (
        select(Review).join(Profile).where(and_(Review.id == review_id, Profile.user_id == user_id))
    )
    result = await db.execute(stmt)
    review = result.scalars().first()

    if review is None:
        raise ReviewNotFoundError(str(review_id))

    if review.status != "complete":
        raise ReviewNotShareableError(review.status)

    now = datetime.now(UTC)

    # Reuse an existing, unexpired link if one already exists.
    stmt = select(ShareLink).where(
        and_(ShareLink.review_id == review_id, ShareLink.expires_at > now)
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()
    if existing is not None:
        return existing

    # Otherwise mint a new link.
    share_link = ShareLink(
        review_id=review_id,
        token=secrets.token_urlsafe(SHARE_TOKEN_BYTES),
        expires_at=now + timedelta(days=SHARE_LINK_EXPIRE_DAYS),
    )
    db.add(share_link)
    await db.commit()
    await db.refresh(share_link)

    log.info("share_link_created", review_id=str(review_id), user_id=str(user_id))
    return share_link


async def get_shared_review(db: AsyncSession, token: str) -> ShareLink | None:
    """Resolve a share token to its ShareLink (with review eager-loaded).

    Returns None if the token is unknown or the link has expired, so callers
    cannot distinguish "never existed" from "expired" (avoids token enumeration).

    Args:
        db: Async database session.
        token: The opaque share token from the public URL.

    Returns:
        The ShareLink with its ``review`` loaded, or None if invalid/expired.
    """
    stmt = select(ShareLink).options(selectinload(ShareLink.review)).where(ShareLink.token == token)
    result = await db.execute(stmt)
    share_link = result.scalars().first()

    if share_link is None:
        return None

    if share_link.expires_at < datetime.now(UTC):
        return None

    return share_link
