from typing import cast
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
    """
    Create a new profile for a user.

    Args:
        db (AsyncSession): The database session.
        user_id (UUID): The ID of the user for whom the profile is being created.
        data (ProfileCreate): The profile information to create.
        resume_filename (str, optional): The filename of the uploaded resume. Defaults to None.
        resume_text (str, optional): The text extracted from the uploaded resume. Defaults to None.

    Returns:
        Profile: The newly created profile instance.
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
    """
    Get a profile by ID, checking ownership.

    Args:
        db (AsyncSession): The database session.
        profile_id (UUID): The ID of the profile to retrieve.
        user_id (UUID): The ID of the user who owns the profile.

    Returns:
        Profile | None: The profile instance if found, otherwise None.
    """
    stmt = select(Profile).where((Profile.id == profile_id) & (Profile.user_id == user_id))
    result = await db.execute(stmt)
    return cast(Profile | None, result.scalars().first())


async def update_profile(
    db: AsyncSession,
    profile_id: UUID,
    user_id: UUID,
    data: ProfileUpdate,
) -> Profile | None:
    """
    Update a profile, checking ownership.

    Args:
        db (AsyncSession): The database session.
        profile_id (UUID): The ID of the profile to update.
        user_id (UUID): The ID of the user who owns the profile.
        data (ProfileUpdate): The profile information to update.

    Returns:
        Profile | None: The updated profile instance if found, otherwise None.
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
    """
    Delete a profile and cascade delete reviews and ingested sources.

    Args:
        db (AsyncSession): The database session.
        profile_id (UUID): The ID of the profile to delete.
        user_id (UUID): The ID of the user who owns the profile.

    Returns:
        bool: True if deleted, False if not found.

    Raises:
        Exception: Re-raises any exception encountered during deletion
            after rolling back the transaction.
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
