from uuid import UUID
import structlog
from sqlalchemy import select

from core.models.profile import Profile
from core.models.review import Review
from core.models.ingested_source import IngestedSource
from api.schemas.profile import ProfileCreate, ProfileUpdate
from rag.retriever.vector_store import VectorStore, collection_name_for_profile

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
    vector_store: VectorStore | None = None,
) -> bool:
    """
    Delete a profile and cascade delete its reviews, ingested sources, and embeddings.

    The relational rows (reviews, ingested sources, profile) are removed inside a
    single Postgres transaction. The profile's embeddings live in a separate
    ChromaDB collection (``profile_<id>``) that shares no transaction with
    Postgres, so it is cleaned up on a best-effort basis *after* the SQL commit
    succeeds: if Chroma cleanup fails we log loudly but do not fail a delete whose
    rows are already gone (see issue #80). Ordering matters — committing SQL first
    means a Chroma failure leaves recoverable orphaned vectors, whereas deleting
    Chroma first could wipe a live profile's vectors if the SQL delete then failed.

    Args:
        db: Async SQLAlchemy session.
        profile_id: ID of the profile to delete.
        user_id: ID of the requesting user, used for the ownership check.
        vector_store: Optional VectorStore to clean up embeddings through.
            Defaults to a new VectorStore; injectable for tests.

    Returns:
        True if the profile was found and deleted, False if it did not exist or
        was not owned by ``user_id``.
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

    except Exception as exc:
        log.error("profile_cascade_delete_failed", profile_id=str(profile_id), error=str(exc))
        await db.rollback()
        raise

    # SQL rows are gone and committed. Now clean up the profile's embeddings.
    # This is best-effort and idempotent: a Chroma failure must not turn a
    # successful delete into a 500, so we log it and move on rather than raise.
    try:
        store = vector_store if vector_store is not None else VectorStore()
        store.delete_collection(collection_name_for_profile(profile_id))
    except Exception as exc:
        log.error(
            "profile_embeddings_cleanup_failed",
            profile_id=str(profile_id),
            error=str(exc),
        )

    return True
