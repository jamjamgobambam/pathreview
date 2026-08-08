from uuid import UUID
import structlog
from sqlalchemy import select

from core.models.profile import Profile
from core.models.review import Review
from core.models.ingested_source import IngestedSource
from api.schemas.profile import ProfileCreate, ProfileUpdate

log = structlog.get_logger()


async def create_profile(
    db,
    user_id: UUID,
    data: ProfileCreate,
    resume_filename: str = None,
    resume_text: str = None,
) -> Profile:
    """
    Create a new profile for a user.

    The profile is persisted immediately and refreshed, so server-generated
    fields such as id, created_at, and updated_at are populated on the
    returned object.

    Args:
        db: Active async SQLAlchemy session.
        user_id: ID of the user who will own the profile.
        data: Validated payload supplying github_username and portfolio_url.
        resume_filename: Original filename of an uploaded resume, if any.
        resume_text: Extracted plain text of an uploaded resume, if any.

    Returns:
        The newly created Profile, refreshed from the database.

    Raises:
        SQLAlchemyError: If the insert or commit fails. The session is not
            rolled back here; the caller is responsible for that.
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
    """
    Get a profile by ID, checking ownership.

    Ownership is enforced in the query itself, so a profile that exists but
    belongs to a different user is indistinguishable from one that does not
    exist. Callers cannot use this to probe for other users' profile IDs.

    Args:
        db: Active async SQLAlchemy session.
        profile_id: ID of the profile to fetch.
        user_id: ID of the requesting user; must match Profile.user_id.

    Returns:
        The matching Profile, or None if no profile with that ID is owned by
        this user.
    """
    stmt = select(Profile).where(
        (Profile.id == profile_id) & (Profile.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def update_profile(
    db,
    profile_id: UUID,
    user_id: UUID,
    data: ProfileUpdate,
) -> Profile | None:
    """
    Update a profile, checking ownership.

    Only fields set on the payload are applied. A None value means "leave
    unchanged", so this cannot be used to clear github_username or
    portfolio_url back to None.

    Args:
        db: Active async SQLAlchemy session.
        profile_id: ID of the profile to update.
        user_id: ID of the requesting user; must own the profile.
        data: Partial update payload. Fields left as None are ignored.

    Returns:
        The updated Profile, or None if no profile with that ID is owned by
        this user.

    Raises:
        SQLAlchemyError: If the commit fails. The session is not rolled back
            here; the caller is responsible for that.
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
    """
    Delete a profile and cascade delete reviews and ingested sources.

    Related Review and IngestedSource rows are removed first, then the profile
    itself, all within a single transaction. If any step fails the transaction
    is rolled back, leaving the profile and its children intact.

    Args:
        db: Active async SQLAlchemy session.
        profile_id: ID of the profile to delete.
        user_id: ID of the requesting user; must own the profile.

    Returns:
        True if the profile was deleted, False if no profile with that ID is
        owned by this user.

    Raises:
        Exception: Any error raised while deleting rows or committing is
            logged as "profile_cascade_delete_failed", the transaction is
            rolled back, and the error is re-raised unchanged.
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
