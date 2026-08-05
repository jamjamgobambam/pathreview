from uuid import UUID

import structlog
from sqlalchemy import select

from api.schemas.profile import ProfileCreate, ProfileUpdate
from core.models.ingested_source import IngestedSource
from core.models.profile import Profile
from core.models.review import Review

log = structlog.get_logger()


async def create_profile(
    db,
    user_id: UUID,
    data: ProfileCreate,
    resume_filename: str = None,
    resume_text: str = None,
) -> Profile:
    """Create and persist a profile for a user.

    Args:
        db: Async SQLAlchemy session used to persist the profile.
        user_id: Unique identifier of the user who owns the profile.
        data: Validated GitHub username and portfolio URL values.
        resume_filename: Original resume filename, or None when unavailable.
        resume_text: Extracted resume text, or None when unavailable.

    Returns:
        The newly persisted and refreshed profile.

    Raises:
        SQLAlchemyError: If the profile cannot be committed or refreshed.
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
    db,
    profile_id: UUID,
    user_id: UUID,
) -> Profile | None:
    """Return a profile when it exists and belongs to the requesting user.

    Args:
        db: Async SQLAlchemy session used to query profiles.
        profile_id: Unique identifier of the profile to retrieve.
        user_id: Unique identifier of the expected profile owner.

    Returns:
        The matching profile, or None when no owned profile is found.

    Raises:
        SQLAlchemyError: If the profile query fails.
    """
    stmt = select(Profile).where((Profile.id == profile_id) & (Profile.user_id == user_id))
    result = await db.execute(stmt)
    return result.scalars().first()


async def update_profile(
    db,
    profile_id: UUID,
    user_id: UUID,
    data: ProfileUpdate,
) -> Profile | None:
    """Update editable fields on a profile owned by the requesting user.

    Args:
        db: Async SQLAlchemy session used to query and persist the profile.
        profile_id: Unique identifier of the profile to update.
        user_id: Unique identifier of the expected profile owner.
        data: Validated profile fields; None-valued fields remain unchanged.

    Returns:
        The refreshed profile, or None when no owned profile is found.

    Raises:
        SQLAlchemyError: If querying, committing, or refreshing fails.
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
    db,
    profile_id: UUID,
    user_id: UUID,
) -> bool:
    """Delete an owned profile and its reviews and ingested sources.

    Args:
        db: Async SQLAlchemy session used for the cascade deletion.
        profile_id: Unique identifier of the profile to delete.
        user_id: Unique identifier of the expected profile owner.

    Returns:
        True when the profile is deleted, or False when it is not found.

    Raises:
        Exception: Re-raised after rollback if a delete or commit operation fails.
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
