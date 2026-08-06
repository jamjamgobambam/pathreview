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
    """
    Create a review for a profile with status="pending".

    Args:
        db: Database session
        profile_id: ID of the profile the review is for
        user_id: ID of the user requesting the review. Accepted for symmetry
            with the other functions in this module but currently unused:
            this function performs no ownership check, so the caller is
            responsible for confirming the profile belongs to the user.

    Returns:
        The created Review, refreshed after the commit so that id, created_at
        and updated_at are populated. status is "pending", while sections and
        overall_score stay None until process_review fills them in.

    Raises:
        sqlalchemy.exc.IntegrityError: If profile_id does not reference an
            existing profile, since reviews.profile_id is a foreign key that
            can't be null. The commit is not wrapped in a try/except, so this
            and any other database error reach the caller with the session
            left un-rolled-back.
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
    """
    Get a review by ID, checking that it belongs to the user's profile.

    Ownership is enforced in the query itself: reviews is joined to profiles
    and profiles.user_id must match, so another user's review is never
    returned rather than being fetched and then rejected.

    Args:
        db: Database session
        review_id: ID of the review to fetch
        user_id: ID of the user who must own the profile the review belongs to

    Returns:
        The matching Review, or None if no review has this ID or the review
        belongs to another user's profile. The caller cannot distinguish
        those two cases, would need to tweak the return case but that is not the current scope.
    """
    stmt = (
        select(Review).join(Profile).where(and_(Review.id == review_id, Profile.user_id == user_id))
    )
    result = await db.execute(stmt)
    review: Review | None = result.scalars().first()
    return review


async def list_reviews(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Review], int]:
    """
    List a user's reviews, newest first, with pagination.

    Ownership is enforced in the query: reviews is joined to profiles and
    profiles.user_id must match, so only the user's own reviews are counted
    and returned.

    Args:
        db: Database session
        user_id: ID of the user whose reviews to list
        page: 1-based page number
        page_size: Maximum number of reviews to return on this page

    Returns:
        A (reviews, total) tuple. reviews holds at most page_size Reviews
        ordered by created_at descending; total is the user's overall review
        count, not the number on this page. A user with no reviews, or a page
        past the last one, gives ([], total) rather than an error.

    Raises:
        sqlalchemy.exc.DBAPIError: If page is below 1, which yields a negative
            SQL OFFSET that PostgreSQL rejects. This function validates
            neither page nor page_size; the reviews route clamps both before
            calling it.
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
    """
    Run the full review pipeline for one review, in the background.

    Registered with background_tasks.add_task in the create review route, so
    nothing awaits the result and the request returns while this is still
    running. Progress reaches the caller only through review.status, which
    clients poll: "processing" once work starts, then "complete" or "failed".

    The review and the profile are looked up independently and never checked
    against each other, so a mismatched pair processes review_id using
    profile_id's sources instead of failing.

    Steps:
    1. Set status="processing"
    2. Run ingestion pipeline on profile's sources
    3. Run agent orchestration
    4. Run RAG retrieval + generation
    5. Run safety checks on output
    6. Set status="complete", store sections in review.sections
    7. On exception: set status="failed", log error

    Args:
        db: Database session. Committed at each status change rather than
            once at the end, so partial progress is visible to other sessions
            before the run finishes.
        review_id: ID of the review to process
        profile_id: ID of the profile whose sources are reviewed

    Returns:
        None. Everything observable is written to the Review row. Returns
        early without changing anything if no review has this ID, and marks
        the review "failed" and returns early if the profile is missing or
        the safety checks reject the generated output.

    Raises:
        Nothing. Every exception is caught and turned into status="failed",
        and the fallback write that records that status is itself wrapped, so
        a database error during error handling is logged and swallowed too.
        A review can therefore stay "processing" indefinitely if that second
        write fails. No failure path populates reviews.error_message, so the
        reason a review failed exists only in the logs.
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
        review.sections = [s.model_dump() for s in sections]
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
    """
    Run ingestion pipeline to extract data from profile sources.
    Returns list of ingested source data.
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
    """
    Run agent orchestration to analyze ingested data.
    Returns agent output with initial analysis.
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
    """
    Run RAG retrieval and generation to create detailed feedback.
    Returns enhanced review output.
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
    """
    Run safety checks on the review output.
    Returns True if all checks pass, False otherwise.
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
