from uuid import UUID
import structlog
import json
from datetime import datetime
from sqlalchemy import select, and_

from core.models.review import Review
from core.models.profile import Profile
from core.models.ingested_source import IngestedSource
from api.schemas.review import FeedbackSection

log = structlog.get_logger()


async def create_review(
    db,
    profile_id: UUID,
    user_id: UUID,
) -> Review:
    """
    Create a new review with status="pending".
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
    db,
    review_id: UUID,
    user_id: UUID,
) -> Review | None:
    """
    Get a review by ID, checking that it belongs to the user's profile.
    """
    stmt = select(Review).join(Profile).where(
        and_(Review.id == review_id, Profile.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_reviews(
    db,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Review], int]:
    """
    List reviews for a user with pagination.
    Returns (reviews, total_count).
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

    return reviews, total


async def process_review(
    db,
    review_id: UUID,
    profile_id: UUID,
) -> None:
    """
    Background task to process a review.
    Steps:
    1. Set status="processing"
    2. Run ingestion pipeline on profile's sources
    3. Run agent orchestration
    4. Run RAG retrieval + generation
    5. Run safety checks on output
    6. Set status="complete", store sections in review.sections
    7. On exception: set status="failed", log error
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


async def _run_ingestion_pipeline(db, profile: Profile) -> list[dict]:
    """
    Run ingestion pipeline to extract data from profile sources.
    Returns list of ingested source data.
    """
    sources = []

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
