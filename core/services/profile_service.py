from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.profile import ProfileCreate, ProfileUpdate
from core.models.ingested_source import IngestedSource
from core.models.profile import Profile
from core.models.review import Review

log = structlog.get_logger()

# The models declare their primary keys as UUID(as_uuid=False), so IDs are stored
# and read back as str, while FastAPI hands the routes a parsed UUID. Both forms
# reach these functions and both compare correctly in the generated SQL.
Id = str | UUID


async def create_profile(
    db: AsyncSession,
    user_id: Id,
    data: ProfileCreate,
    resume_filename: str | None = None,
    resume_text: str | None = None,
) -> Profile:
    """
    Create a new profile for a user.

    Args:
        db: Database session
        user_id: ID of the user creating the profile
        data: ProfileCreate schema with profile data
        resume_filename: Optional filename of the uploaded resume
        resume_text: Optional text extracted from the resume

    Returns:
        The created Profile object, refreshed with database-generated fields.
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
    profile_id: Id,
    user_id: Id,
) -> Profile | None:
    """
    Get a profile by ID, checking ownership.

    Args:
        db: Database session
        profile_id: ID of the profile to fetch
        user_id: ID of the user who must own the profile

    Returns:
        The matching Profile, or None if it does not exist or belongs to
        another user
    """
    stmt = select(Profile).where((Profile.id == profile_id) & (Profile.user_id == user_id))
    result = await db.execute(stmt)
    profile: Profile | None = result.scalars().first()
    return profile


async def update_profile(
    db: AsyncSession,
    profile_id: Id,
    user_id: Id,
    data: ProfileUpdate,
) -> Profile | None:
    """
    Update a profile, checking ownership.
    Only github_username and portfolio_url are updatable; a field left as None
    is kept at its current value rather than cleared.

    Args:
        db: Database session
        profile_id: ID of the profile to update
        user_id: ID of the user who must own the profile
        data: ProfileUpdate with the fields to change

    Returns:
        The updated Profile, or None if it does not exist or belongs to
        another user
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
    profile_id: Id,
    user_id: Id,
) -> bool:
    """
    Delete a profile along with its reviews and ingested sources.

    Args:
        db: Database session
        profile_id: ID of the profile to delete
        user_id: ID of the user who must own the profile

    Returns:
        True if the profile was deleted, False if it does not exist or
        belongs to another user

    Raises:
        Exception: Re-raised after rolling back the transaction if any part
            of the delete fails
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
