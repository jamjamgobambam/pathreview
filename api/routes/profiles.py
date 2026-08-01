import mimetypes
from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from api.middleware.auth import get_current_user
from api.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from core.config import settings
from core.database import get_db
from core.models.user import User
from core.services.profile_service import (
    create_profile,
    delete_profile,
    get_profile,
    update_profile,
)
from ingestion.embeddings.provider import get_embedding_provider
from ingestion.pipeline import IngestionPipeline
from rag.retriever.vector_store import VectorStore

log = structlog.get_logger()

router = APIRouter(prefix="/profiles", tags=["profiles"])

PORTFOLIO_COLLECTION_NAME = "portfolio_sources"

_vector_store = VectorStore()

DbSession = Annotated[Any, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_ingestion_pipeline(db: DbSession) -> IngestionPipeline:
    """Build an IngestionPipeline for the current request."""
    collection = _vector_store.get_collection(PORTFOLIO_COLLECTION_NAME)
    embedding_provider = get_embedding_provider("mock" if not settings.openai_api_key else "openai")
    return IngestionPipeline(
        vector_db=collection,
        db_session=db,
        embedding_provider=embedding_provider,
    )


IngestionPipelineDep = Annotated[IngestionPipeline, Depends(get_ingestion_pipeline)]


@router.post("", response_model=ProfileResponse)
async def create_profile_endpoint(
    current_user: CurrentUser,
    db: DbSession,
    pipeline: IngestionPipelineDep,
    github_username: str = Form(default=None),
    portfolio_url: str = Form(default=None),
    resume_file: Annotated[UploadFile, File()] = None,
):
    """
    Create a new profile with optional resume upload.
    Resume must be PDF or Markdown.
    Returns 422 if file is not PDF or markdown.
    """
    try:
        resume_filename = None
        resume_text = None

        if resume_file:
            # Check file type
            file_mime = resume_file.content_type or mimetypes.guess_type(resume_file.filename)[0]

            if file_mime not in ["application/pdf", "text/markdown", "text/plain"]:
                log.warning(
                    "profile_creation_invalid_file_type",
                    file_type=file_mime,
                    user_id=str(current_user.id),
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Resume must be a PDF or Markdown file",
                )

            # Read file content
            content = await resume_file.read()

            # Parse resume text
            if file_mime == "application/pdf":
                try:
                    import PyPDF2

                    pdf_reader = PyPDF2.PdfReader(content)
                    resume_text = "\n".join(page.extract_text() for page in pdf_reader.pages)
                except Exception as exc:
                    log.error("pdf_parsing_failed", error=str(exc))
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Failed to parse PDF resume",
                    ) from exc
            else:
                # Markdown or plain text
                resume_text = content.decode("utf-8")

            resume_filename = resume_file.filename

        # Create profile
        profile_data = ProfileCreate(
            github_username=github_username,
            portfolio_url=portfolio_url,
        )

        new_profile = await create_profile(
            db=db,
            user_id=current_user.id,
            data=profile_data,
            resume_filename=resume_filename,
            resume_text=resume_text,
        )

        log.info(
            "profile_created",
            profile_id=str(new_profile.id),
            user_id=str(current_user.id),
        )

        if portfolio_url:
            try:
                await pipeline.ingest_portfolio_url(
                    profile_id=str(new_profile.id),
                    url=portfolio_url,
                )
            except Exception as exc:
                # Best-effort: a slow/unreachable portfolio site must not
                # fail profile creation.
                log.warning(
                    "portfolio_ingestion_failed",
                    profile_id=str(new_profile.id),
                    portfolio_url=portfolio_url,
                    error=str(exc),
                )

        return ProfileResponse.model_validate(new_profile)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("profile_creation_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile",
        ) from exc


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile_endpoint(
    profile_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Get a profile by ID.
    Returns 404 if not found or not owned by current user.
    """
    try:
        profile = await get_profile(db=db, profile_id=profile_id, user_id=current_user.id)

        if not profile:
            log.warning(
                "profile_not_found",
                profile_id=str(profile_id),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        return ProfileResponse.model_validate(profile)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("get_profile_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile",
        ) from exc


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile_endpoint(
    profile_id: UUID,
    data: ProfileUpdate,
    current_user: CurrentUser,
    db: DbSession,
    pipeline: IngestionPipelineDep,
):
    """
    Update a profile.
    Returns 404 if not found or not owned by current user.
    """
    try:
        updated_profile = await update_profile(
            db=db,
            profile_id=profile_id,
            user_id=current_user.id,
            data=data,
        )

        if not updated_profile:
            log.warning(
                "profile_not_found",
                profile_id=str(profile_id),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        log.info(
            "profile_updated",
            profile_id=str(profile_id),
            user_id=str(current_user.id),
        )

        if data.portfolio_url:
            try:
                await pipeline.ingest_portfolio_url(
                    profile_id=str(updated_profile.id),
                    url=data.portfolio_url,
                )
            except Exception as exc:
                log.warning(
                    "portfolio_ingestion_failed",
                    profile_id=str(updated_profile.id),
                    portfolio_url=data.portfolio_url,
                    error=str(exc),
                )

        return ProfileResponse.model_validate(updated_profile)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("profile_update_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        ) from exc


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_endpoint(
    profile_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Delete a profile and cascade delete reviews and ingested sources.
    Returns 404 if not found or not owned by current user.
    """
    try:
        success = await delete_profile(
            db=db,
            profile_id=profile_id,
            user_id=current_user.id,
        )

        if not success:
            log.warning(
                "profile_not_found",
                profile_id=str(profile_id),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        log.info(
            "profile_deleted",
            profile_id=str(profile_id),
            user_id=str(current_user.id),
        )

    except HTTPException:
        raise
    except Exception as exc:
        log.error("profile_deletion_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete profile",
        ) from exc
