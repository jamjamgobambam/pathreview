"""End-to-end tests for IngestionPipeline.ingest_resume() (issue #18).

Covers the full resume ingestion flow: parse, chunk, embed, and store,
using a sample resume fixture, plus the already-ingested skip path.

Note: db_session.query("IngestedSource") in pipeline.py's _check_skip()
queries with a string instead of the model class, so a mocked db_session's
.first() always returns a truthy Mock unless configured otherwise. These
tests configure db_session explicitly to work around that rather than
changing pipeline.py, which is out of scope for this issue.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sample_resumes"
FIXTURE_PATH = FIXTURES_DIR / "resume.txt"
NO_EXPERIENCE_FIXTURE_PATH = FIXTURES_DIR / "resume_no_experience.txt"


def _make_pipeline() -> tuple[IngestionPipeline, Mock]:
    """Build a pipeline with a db_session mocked to never find an existing match."""
    db_session = Mock()
    db_session.query.return_value.filter_by.return_value.first.return_value = None
    vector_db = Mock()

    pipeline = IngestionPipeline(
        vector_db=vector_db,
        db_session=db_session,
        embedding_provider=MockEmbeddingProvider(),
    )
    return pipeline, vector_db


@pytest.mark.integration
def test_ingest_resume_end_to_end() -> None:
    resume_text = FIXTURE_PATH.read_text()
    pipeline, vector_db = _make_pipeline()

    result = pipeline.ingest_resume(
        profile_id="test-profile",
        content=resume_text,
        filename="resume.txt",
    )

    assert result.skipped is False
    assert result.chunk_count > 0
    assert vector_db.add.call_count == result.chunk_count


@pytest.mark.integration
def test_ingest_resume_with_no_work_experience_section() -> None:
    resume_text = NO_EXPERIENCE_FIXTURE_PATH.read_text()
    pipeline, vector_db = _make_pipeline()

    result = pipeline.ingest_resume(
        profile_id="test-profile-no-experience",
        content=resume_text,
        filename="resume_no_experience.txt",
    )

    assert result.skipped is False
    assert result.chunk_count > 0
    assert vector_db.add.call_count == result.chunk_count


@pytest.mark.integration
def test_ingest_resume_skips_if_already_ingested() -> None:
    resume_text = FIXTURE_PATH.read_text()

    db_session = Mock()
    # First call: no existing record found, so ingestion proceeds.
    # Second call: a record is found, so the pipeline should skip.
    db_session.query.return_value.filter_by.return_value.first.side_effect = [None, Mock()]
    vector_db = Mock()

    pipeline = IngestionPipeline(
        vector_db=vector_db,
        db_session=db_session,
        embedding_provider=MockEmbeddingProvider(),
    )

    first_result = pipeline.ingest_resume(
        profile_id="test-profile",
        content=resume_text,
        filename="resume.txt",
    )
    second_result = pipeline.ingest_resume(
        profile_id="test-profile",
        content=resume_text,
        filename="resume.txt",
    )

    assert first_result.skipped is False
    assert second_result.skipped is True
    assert second_result.chunk_count == 0
    # Only the first call should have generated and stored embeddings.
    assert vector_db.add.call_count == first_result.chunk_count
