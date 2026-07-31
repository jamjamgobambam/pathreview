import asyncio
from uuid import UUID
import structlog
from sqlalchemy import select

from core.config import settings
from core.database import SyncSessionLocal
from core.models.profile import Profile
from core.models.review import Review
from core.models.ingested_source import IngestedSource
from api.schemas.profile import ProfileCreate, ProfileUpdate
from ingestion.embeddings.provider import get_embedding_provider
from ingestion.pipeline import IngestionPipeline
from rag.retriever.vector_store import VectorStore

log = structlog.get_logger()


def _ingest_portfolio(profile_id: str, portfolio_url: str) -> None:
    """
    Fetch and embed a profile's portfolio page.

    Runs synchronously against the ingestion pipeline. Failures (unreachable
    site, non-HTML content, etc.) are logged and swallowed so that a bad
    portfolio URL never breaks profile creation/update.
    """
    try:
        vector_db = VectorStore().get_collection(f"profile_{profile_id}")
        with SyncSessionLocal() as session:
            pipeline = IngestionPipeline(
                vector_db=vector_db,
                db_session=session,
                embedding_provider=get_embedding_provider(settings.llm_provider),
            )
            pipeline.ingest_portfolio(profile_id=profile_id, url=portfolio_url)
    except Exception as exc:
        log.warning(
            "portfolio_ingestion_failed",
            profile_id=profile_id,
            portfolio_url=portfolio_url,
            error=str(exc),
        )


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

    if profile.portfolio_url:
        await asyncio.to_thread(_ingest_portfolio, str(profile.id), profile.portfolio_url)

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

    if data.portfolio_url:
        await asyncio.to_thread(_ingest_portfolio, str(profile.id), profile.portfolio_url)

    return profile


async def delete_profile(
    db,
    profile_id: UUID,
    user_id: UUID,
) -> bool:
    """
    Delete a profile and cascade delete reviews and ingested sources.
    Returns True if deleted, False if not found.
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
