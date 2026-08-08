"""Service layer for creating and resolving public share links for reviews."""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.models.profile import Profile
from core.models.review import Review
from core.models.share_link import ShareLink

log = structlog.get_logger()

# How long a share link stays valid before it expires.
SHARE_LINK_TTL = timedelta(days=30)

# Number of random bytes used to generate a share token. secrets.token_urlsafe(32)
# yields a 43-character opaque, URL-safe string.
SHARE_TOKEN_BYTES = 32


class ShareLinkExpiredError(Exception):
    """Raised when a share token exists but is past its expiry."""


def _now() -> datetime:
    """Current time as a timezone-aware UTC datetime.

    The ``share_links.expires_at`` column is ``timestamptz``, so values read back
    from Postgres are timezone-aware. Comparing those against a naive
    ``datetime.utcnow()`` raises ``TypeError``, so we standardize on aware UTC.
    """
    return datetime.now(UTC)


def build_share_url(token: str) -> str:
    """Build the absolute, user-facing share URL for a token."""
    base = settings.frontend_base_url.rstrip("/")
    return f"{base}/shared/{token}"


async def create_share_link(
    db: AsyncSession,
    review_id: UUID,
    user_id: UUID,
) -> ShareLink | None:
    """Create (or reuse) a share link for a review the user owns.

    Returns the ``ShareLink`` on success, or ``None`` if the review does not exist
    or is not owned by ``user_id`` (the caller should translate this to a 404).

    Behavior:
    - Verifies ownership via the same profile join used by ``get_review``.
    - Deletes any expired links for the review so the table stays bounded.
    - Reuses an existing non-expired link instead of minting a duplicate.
    """
    # Ownership check: the review must join to a profile owned by this user.
    ownership_stmt = (
        select(Review.id)
        .join(Profile)
        .where(and_(Review.id == review_id, Profile.user_id == user_id))
    )
    owned = (await db.execute(ownership_stmt)).scalars().first()
    if owned is None:
        return None

    now = _now()

    # Clean up expired links for this review before minting a new one.
    await db.execute(
        delete(ShareLink).where(and_(ShareLink.review_id == review_id, ShareLink.expires_at < now))
    )

    # Reuse an existing, still-valid link if one exists.
    existing_stmt = (
        select(ShareLink)
        .where(and_(ShareLink.review_id == review_id, ShareLink.expires_at > now))
        .order_by(ShareLink.expires_at.desc())
    )
    existing: ShareLink | None = (await db.execute(existing_stmt)).scalars().first()
    if existing is not None:
        await db.commit()
        log.info("share_link_reused", review_id=str(review_id), share_link_id=str(existing.id))
        return existing

    # Mint a fresh link.
    share_link = ShareLink(
        review_id=review_id,
        token=secrets.token_urlsafe(SHARE_TOKEN_BYTES),
        expires_at=now + SHARE_LINK_TTL,
    )
    db.add(share_link)
    await db.commit()
    await db.refresh(share_link)
    log.info("share_link_created", review_id=str(review_id), share_link_id=str(share_link.id))
    return share_link


async def get_review_by_share_token(db: AsyncSession, token: str) -> Review | None:
    """Resolve a share token to its review, with no user scoping (public access).

    Returns the ``Review`` when the token is valid and unexpired. Raises
    ``ShareLinkExpiredError`` when the token exists but has expired (caller should
    translate to 410). Returns ``None`` when the token is unknown (caller -> 404).
    """
    stmt = select(ShareLink).where(ShareLink.token == token)
    share_link = (await db.execute(stmt)).scalars().first()

    if share_link is None:
        return None

    if share_link.expires_at < _now():
        raise ShareLinkExpiredError()

    review_stmt = select(Review).where(Review.id == share_link.review_id)
    review: Review | None = (await db.execute(review_stmt)).scalars().first()
    return review
