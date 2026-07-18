from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.profile import ProfileCreate, ProfileUpdate
from core.models.ingested_source import IngestedSource
from core.models.profile import Profile
from core.models.review import Review

log = structlog.get_logger()


async def create_profile(
    db: AsyncSession,
    user_id: UUID,
    data: ProfileCreate,
    resume_filename: str | None = None,
    resume_text: str | None = None,
) -> Profile:
    """Create a new profile for a user.

    Args:
        db: Database session used to persist the new profile.
        user_id: ID of the user who will own the profile.
        data: Profile fields (GitHub username, portfolio URL) submitted in the
            create request.
        resume_filename: Original filename of the uploaded resume, if provided.
        resume_text: Extracted text content of the resume, if provided.

    Returns:
        The newly created Profile, with its generated ID and timestamps
        populated.
    """
    profile = Profile(
        user_id=user_id,
        github_username=data.github_username,
        portfolio_url=data.portfolio_url,
        resume_filename=resume_filename,
        resume_text=resume_text,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_profile(
    db: AsyncSession,
    profile_id: UUID,
    user_id: UUID,
) -> Profile | None:
    """Get a profile by ID, checking ownership.

    Args:
        db: Database session used to query the profile.
        profile_id: ID of the profile to fetch.
        user_id: ID of the user who must own the profile.

    Returns:
        The matching Profile, or None if no profile with that ID exists
        for this user.
    """
    stmt = select(Profile).where((Profile.id == profile_id) & (Profile.user_id == user_id))
    result = await db.execute(stmt)
    # pre-commit's isolated mypy env lacks SQLAlchemy stubs, so it can't
    # infer this as Profile | None the way the project's local mypy does.
    return result.scalars().first()  # type: ignore[no-any-return]


async def update_profile(
    db: AsyncSession,
    profile_id: UUID,
    user_id: UUID,
    data: ProfileUpdate,
) -> Profile | None:
    """Update a profile, checking ownership.

    Only fields present in `data` are applied, so a partial update (e.g.
    changing just the portfolio URL) leaves other fields untouched.

    Args:
        db: Database session used to fetch and persist the profile.
        profile_id: ID of the profile to update.
        user_id: ID of the user who must own the profile.
        data: Fields to update; `None` values are left unchanged.

    Returns:
        The updated Profile, or None if no profile with that ID exists
        for this user.
    """
    profile = await get_profile(db, profile_id, user_id)
    if not profile:
        return None

    if data.github_username is not None:
        profile.github_username = data.github_username
    if data.portfolio_url is not None:
        profile.portfolio_url = data.portfolio_url

    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def delete_profile(
    db: AsyncSession,
    profile_id: UUID,
    user_id: UUID,
) -> bool:
    """Delete a profile and cascade delete reviews and ingested sources.

    Args:
        db: Database session used to fetch and delete records.
        profile_id: ID of the profile to delete.
        user_id: ID of the user who must own the profile.

    Returns:
        True if the profile (and its reviews/ingested sources) was
        deleted, False if no profile with that ID exists for this user.

    Raises:
        Exception: If deletion fails partway through. The transaction is
            rolled back and the original exception is re-raised after
            being logged.
    """
    profile = await get_profile(db, profile_id, user_id)
    if not profile:
        return False

    try:
        # Delete related reviews
        stmt = select(Review).where(Review.profile_id == profile_id)
        result = await db.execute(stmt)
        reviews = result.scalars().all()
        for review in reviews:
            await db.delete(review)

        # Delete related ingested sources
        stmt = select(IngestedSource).where(IngestedSource.profile_id == profile_id)
        result = await db.execute(stmt)
        sources = result.scalars().all()
        for source in sources:
            await db.delete(source)

        # Delete profile
        await db.delete(profile)
        await db.commit()

        log.info("profile_deleted_cascade", profile_id=str(profile_id))
        return True

    except Exception as exc:
        log.error("profile_cascade_delete_failed", profile_id=str(profile_id), error=str(exc))
        await db.rollback()
        raise
