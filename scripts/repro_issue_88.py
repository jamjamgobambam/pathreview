"""Reproduction script for issue #88.

Demonstrates that POST /reviews and the background review-processing job
never check whether a profile has any ingested content. Run with:

    PYTHONPATH=. python scripts/repro_issue_88.py

Requires the project's dev dependencies to be installed (see docs/SETUP.md).
No live database is needed -- this exercises the route/service functions
directly with mocked DB sessions, the same pattern used in
tests/unit/test_review_service.py.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from api.routes.reviews import create_review_endpoint
from api.schemas.review import ReviewCreate
from core.services.review_service import process_review


async def repro_endpoint_has_no_validation() -> None:
    print("\n=== Step 1: POST /reviews for a profile with no content ===")

    profile_id = uuid4()
    user_id = uuid4()
    data = ReviewCreate(profile_id=profile_id)

    mock_db = AsyncMock()
    mock_db.add = Mock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    mock_bg = Mock()
    mock_bg.add_task = Mock()

    mock_user = Mock()
    mock_user.id = user_id

    with patch("core.services.review_service.Review") as mock_review_cls:
        instance = mock_review_cls.return_value
        instance.id = uuid4()
        instance.profile_id = profile_id
        instance.status = "pending"
        instance.sections = None
        instance.overall_score = None
        instance.error_message = None
        instance.created_at = datetime.utcnow()
        instance.updated_at = datetime.utcnow()

        result = await create_review_endpoint(data, mock_bg, mock_user, mock_db)

    print(f"response status: {result.status}")
    print(f"background task scheduled: {mock_bg.add_task.called}")
    print("=> Endpoint never looked up the Profile, so it can't know it has no content.")


async def repro_processing_fabricates_feedback() -> None:
    print("\n=== Step 2: background processing for that same empty profile ===")

    review_id = uuid4()
    profile_id = uuid4()

    mock_review = Mock()
    mock_review.id = review_id
    mock_review.status = "pending"

    mock_profile = Mock()
    mock_profile.id = profile_id
    mock_profile.github_username = None
    mock_profile.portfolio_url = None
    mock_profile.resume_text = None
    mock_profile.resume_filename = None

    mock_db = AsyncMock()
    mock_db.add = Mock()
    mock_db.commit = AsyncMock()

    call_count = {"n": 0}

    async def fake_execute(_stmt):
        call_count["n"] += 1
        result = Mock()
        if call_count["n"] == 1:
            result.scalars.return_value.first.return_value = mock_review
        else:
            result.scalars.return_value.first.return_value = mock_profile
        return result

    mock_db.execute = fake_execute

    await process_review(mock_db, review_id, profile_id)

    print(f"final review.status: {mock_review.status}")
    print(f"sections generated: {len(mock_review.sections) if mock_review.sections else 0}")
    print(f"overall_score: {mock_review.overall_score}")
    print("=> Completed with fabricated, generic feedback -- no error surfaced anywhere.")


async def main() -> None:
    await repro_endpoint_has_no_validation()
    await repro_processing_fabricates_feedback()


if __name__ == "__main__":
    asyncio.run(main())
