import json
from datetime import datetime
from uuid import UUID

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.review import FeedbackSection
from core.models.ingested_source import IngestedSource
from core.models.profile import Profile
from core.models.review import Review

log = structlog.get_logger()


async def create_review(
    db: AsyncSession,
    profile_id: UUID,
    user_id: UUID,
) -> Review:
    """Create a new review with status="pending".

    Args:
        db: Database session used to persist the new review.
        profile_id: ID of the profile this review is for.
        user_id: ID of the requesting user. Currently unused — no
            ownership check is performed against profile_id.

    Returns:
        The newly created Review, with status "pending" and no sections
        or score yet.
    """
    review = Review(
        profile_id=profile_id,
        status="pending",
        sections=None,
        overall_score=None,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def get_review(
    db: AsyncSession,
    review_id: UUID,
    user_id: UUID,
) -> Review | None:
    """Get a review by ID, checking that it belongs to the user's profile.

    Args:
        db: Database session used to query the review.
        review_id: ID of the review to fetch.
        user_id: ID of the user who must own the review's profile.

    Returns:
        The matching Review, or None if no review with that ID exists
        for a profile owned by this user.
    """
    stmt = (
        select(Review).join(Profile).where(and_(Review.id == review_id, Profile.user_id == user_id))
    )
    result = await db.execute(stmt)
    # pre-commit's isolated mypy env lacks SQLAlchemy stubs, so it can't
    # infer this as Review | None the way the project's local mypy does.
    return result.scalars().first()  # type: ignore[no-any-return]


async def list_reviews(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Review], int]:
    """List reviews for a user with pagination.

    Results are ordered by creation date, newest first.

    Args:
        db: Database session used to query reviews.
        user_id: ID of the user whose reviews are listed.
        page: 1-indexed page number to fetch.
        page_size: Number of reviews per page.

    Returns:
        A tuple of (reviews for the requested page, total count of
        reviews across all pages).
    """
    offset = (page - 1) * page_size

    # Get total count
    count_stmt = select(Review).join(Profile).where(Profile.user_id == user_id)
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    # Get paginated results
    stmt = (
        select(Review)
        .join(Profile)
        .where(Profile.user_id == user_id)
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    reviews = result.scalars().all()

    return list(reviews), total


async def process_review(
    db: AsyncSession,
    review_id: UUID,
    profile_id: UUID,
) -> None:
    """Background task to process a review.

    Runs the full pipeline for a single review:
    1. Set status="processing"
    2. Run ingestion pipeline on the profile's sources
    3. Run agent orchestration
    4. Run RAG retrieval + generation
    5. Run safety checks on the generated output
    6. Set status="complete" and store sections + score on the review

    If the review or profile can't be found, or the safety checks
    fail, the review's status is set to "failed" (except when the
    review itself is missing, in which case there's no review to
    update) and processing stops early.

    Args:
        db: Database session used for all reads/writes in this pipeline.
        review_id: ID of the review to process.
        profile_id: ID of the profile the review is generated from.

    Returns:
        None. This function never raises — any unexpected exception
        during processing is caught, logged, and used to mark the
        review "failed" on a best-effort basis (that status update
        itself is wrapped in its own try/except, so a failure there is
        only logged, not propagated).
    """
    try:
        # Get the review
        stmt = select(Review).where(Review.id == review_id)
        result = await db.execute(stmt)
        review = result.scalars().first()

        if not review:
            log.error("review_not_found_for_processing", review_id=str(review_id))
            return

        # Get the profile
        stmt = select(Profile).where(Profile.id == profile_id)
        result = await db.execute(stmt)
        profile = result.scalars().first()

        if not profile:
            log.error("profile_not_found_for_processing", profile_id=str(profile_id))
            review.status = "failed"
            db.add(review)
            await db.commit()
            return

        # Step 1: Set status to processing
        review.status = "processing"
        db.add(review)
        await db.commit()

        log.info("review_processing_started", review_id=str(review_id), profile_id=str(profile_id))

        # Step 2: Run ingestion pipeline
        ingestion_results = await _run_ingestion_pipeline(db, profile)
        log.info(
            "ingestion_pipeline_completed",
            review_id=str(review_id),
            sources_count=len(ingestion_results),
        )

        # Step 3: Run agent orchestration
        agent_output = await _run_agent_orchestration(profile, ingestion_results)
        log.info(
            "agent_orchestration_completed",
            review_id=str(review_id),
            sections_count=len(agent_output.get("sections", [])),
        )

        # Step 4: Run RAG retrieval + generation
        rag_output = await _run_rag_retrieval_generation(profile, ingestion_results, agent_output)
        log.info("rag_retrieval_completed", review_id=str(review_id))

        # Step 5: Run safety checks
        safety_checks_passed = await _run_safety_checks(rag_output)
        if not safety_checks_passed:
            log.warning("safety_checks_failed", review_id=str(review_id))
            review.status = "failed"
            db.add(review)
            await db.commit()
            return

        # Step 6: Set status to complete and store sections
        sections_data = rag_output.get("sections", [])
        sections = [
            FeedbackSection(
                section_name=s.get("section_name", ""),
                content=s.get("content", ""),
                confidence=s.get("confidence", 0.0),
                suggestions=s.get("suggestions", []),
            )
            for s in sections_data
        ]

        review.status = "complete"
        # Pre-existing mismatch: Review.sections is typed as a single dict
        # in the model (core/models/review.py), but a list of section
        # dicts is stored here. Out of scope for this docstring change;
        # the model's column type likely needs a migration to fix properly.
        review.sections = [s.model_dump() for s in sections]  # type: ignore[assignment]
        review.overall_score = rag_output.get("overall_score", None)
        review.updated_at = datetime.utcnow()

        db.add(review)
        await db.commit()

        log.info(
            "review_processing_completed",
            review_id=str(review_id),
            overall_score=review.overall_score,
        )

    except Exception as exc:
        log.error("review_processing_failed", review_id=str(review_id), error=str(exc))
        try:
            stmt = select(Review).where(Review.id == review_id)
            result = await db.execute(stmt)
            review = result.scalars().first()
            if review:
                review.status = "failed"
                review.updated_at = datetime.utcnow()
                db.add(review)
                await db.commit()
        except Exception as e:
            log.error("review_status_update_failed", review_id=str(review_id), error=str(e))


async def _run_ingestion_pipeline(db: AsyncSession, profile: Profile) -> list[dict]:
    """Run ingestion pipeline to extract data from profile sources.

    Each available source (GitHub, portfolio URL, resume) is ingested
    independently: a data dict is appended to the returned list and a
    matching IngestedSource record is added to the db session for
    persistence. A failure ingesting one source is logged and skipped
    rather than aborting the others.

    Note:
        GitHub and portfolio ingestion currently store placeholder text
        rather than real API/scraping data. Resume ingestion is real —
        it stores the profile's actual `resume_text`.

    Args:
        db: Database session used to persist IngestedSource records.
        profile: Profile whose sources (`github_username`,
            `portfolio_url`, `resume_text`) are ingested if present.

    Returns:
        List of source data dicts, one per successfully ingested
        source. Empty if the profile has no sources or all ingestion
        attempts failed.
    """
    sources: list[dict] = []

    # Ingest from GitHub if available
    if profile.github_username:
        try:
            # Placeholder: actual GitHub ingestion logic
            github_data = {
                "source_type": "github",
                "username": profile.github_username,
                "data": f"GitHub profile data for {profile.github_username}",
            }
            sources.append(github_data)

            # Store in database
            ingested = IngestedSource(
                profile_id=profile.id,
                source_type="github",
                raw_data=json.dumps(github_data),
            )
            db.add(ingested)
        except Exception as exc:
            log.error(
                "github_ingestion_failed",
                username=profile.github_username,
                error=str(exc),
            )

    # Ingest from portfolio URL if available
    if profile.portfolio_url:
        try:
            # Placeholder: actual portfolio ingestion logic
            portfolio_data = {
                "source_type": "portfolio",
                "url": profile.portfolio_url,
                "data": f"Portfolio data from {profile.portfolio_url}",
            }
            sources.append(portfolio_data)

            # Store in database
            ingested = IngestedSource(
                profile_id=profile.id,
                source_type="portfolio",
                raw_data=json.dumps(portfolio_data),
            )
            db.add(ingested)
        except Exception as exc:
            log.error(
                "portfolio_ingestion_failed",
                url=profile.portfolio_url,
                error=str(exc),
            )

    # Ingest from resume if available
    if profile.resume_text:
        try:
            resume_data = {
                "source_type": "resume",
                "filename": profile.resume_filename,
                "data": profile.resume_text,
            }
            sources.append(resume_data)

            # Store in database
            ingested = IngestedSource(
                profile_id=profile.id,
                source_type="resume",
                raw_data=json.dumps(resume_data),
            )
            db.add(ingested)
        except Exception as exc:
            log.error(
                "resume_ingestion_failed",
                filename=profile.resume_filename,
                error=str(exc),
            )

    await db.commit()
    return sources


async def _run_agent_orchestration(profile: Profile, ingestion_results: list[dict]) -> dict:
    """Run agent orchestration to analyze ingested data.

    Note:
        This is currently a placeholder — it returns a fixed set of
        sections and score regardless of the inputs.

    Args:
        profile: Profile being analyzed. Currently unused by the
            placeholder implementation.
        ingestion_results: Ingested source data from
            `_run_ingestion_pipeline`. Currently unused by the
            placeholder implementation.

    Returns:
        A dict with a "sections" list (each a dict with section_name,
        content, confidence, and suggestions) and an "overall_score".
    """
    # Placeholder: actual agent orchestration logic
    return {
        "sections": [
            {
                "section_name": "Technical Skills",
                "content": "Analysis of technical skills from ingested sources",
                "confidence": 0.8,
                "suggestions": ["Add more detail on AI/ML experience"],
            },
            {
                "section_name": "Project Experience",
                "content": "Analysis of project experience",
                "confidence": 0.75,
                "suggestions": ["Include measurable impact metrics"],
            },
        ],
        "overall_score": 0.75,
    }


async def _run_rag_retrieval_generation(
    profile: Profile,
    ingestion_results: list[dict],
    agent_output: dict,
) -> dict:
    """Run RAG retrieval and generation to create detailed feedback.

    Note:
        This is currently a placeholder — it returns a fixed set of
        sections and score regardless of the inputs. In production this
        would embed ingested content, store it in a vector DB, retrieve
        relevant context, and generate feedback with an LLM.

    Args:
        profile: Profile the review is being generated for. Currently
            unused by the placeholder implementation.
        ingestion_results: Ingested source data from
            `_run_ingestion_pipeline`. Currently unused by the
            placeholder implementation.
        agent_output: Output from `_run_agent_orchestration`. Currently
            unused by the placeholder implementation.

    Returns:
        A dict with a "sections" list (each a dict with section_name,
        content, confidence, and suggestions) and an "overall_score".
    """
    # Placeholder: actual RAG logic
    # In production, this would:
    # 1. Embed ingested content
    # 2. Store in vector DB
    # 3. Retrieve relevant context
    # 4. Generate detailed feedback using LLM

    return {
        "sections": [
            {
                "section_name": "Technical Skills",
                "content": "Detailed feedback on technical skills based on portfolio analysis",
                "confidence": 0.85,
                "suggestions": [
                    "Add more detail on AI/ML experience",
                    "Include specific technologies and frameworks",
                ],
            },
            {
                "section_name": "Project Experience",
                "content": "Detailed feedback on project experience and impact",
                "confidence": 0.8,
                "suggestions": [
                    "Include measurable impact metrics",
                    "Add links to project repositories",
                ],
            },
            {
                "section_name": "Career Growth",
                "content": "Feedback on career progression and development",
                "confidence": 0.78,
                "suggestions": [
                    "Document learning from each role",
                    "Highlight growth in responsibilities",
                ],
            },
        ],
        "overall_score": 0.81,
    }


async def _run_safety_checks(output: dict) -> bool:
    """Run safety checks on the review output.

    Validates that sections exist and each has a non-empty
    `section_name` and `content`, and that `confidence` is within
    [0, 1]. Any unexpected exception during validation is caught and
    treated as a failed check rather than propagated.

    Args:
        output: Review output dict with a "sections" list, where each
            section is a dict with "section_name", "content", and
            "confidence" keys.

    Returns:
        True if all checks pass, False if any check fails (including on
        an unexpected error during validation).
    """
    # Placeholder: actual safety checks logic
    # In production, this would:
    # 1. Check for personally identifiable information
    # 2. Validate feedback tone and constructiveness
    # 3. Check for bias in recommendations
    # 4. Ensure compliance with guidelines

    try:
        # Basic validation
        if not output.get("sections"):
            log.warning("safety_check_failed_no_sections")
            return False

        for section in output.get("sections", []):
            if not section.get("section_name") or not section.get("content"):
                log.warning("safety_check_failed_incomplete_section", section=section)
                return False

            confidence = section.get("confidence", 0)
            if not (0 <= confidence <= 1):
                log.warning("safety_check_failed_invalid_confidence", confidence=confidence)
                return False

        log.info("safety_checks_passed")
        return True

    except Exception as exc:
        log.error("safety_checks_error", error=str(exc))
        return False
