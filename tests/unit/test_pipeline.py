"""
Week 9 coverage tests for the fix to issue #6: Duplicate embeddings
generated when re-ingesting the same repository.
https://github.com/ascherj/pathreview/issues/6

Covers, per PLAN.md:
  1. Changed content does not incorrectly skip.
  2. _record_ingested_source actually persists a row.
  3. A profile with no prior rows proceeds normally.

Plus two isolated unit tests of the rewritten helpers themselves
(_check_skip and _record_ingested_source), which pin down each
helper's behavior independent of the full ingest_resume flow.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.ingested_source import IngestedSource
from ingestion.pipeline import IngestionPipeline

SAMPLE_RESUME_MD = """
Jane Doe
Software Engineer
jane.doe@example.com

Experience:
- Software Engineer at TechCorp (2022-2024)
  Built REST APIs using Python and FastAPI.

Skills: Python, JavaScript, React, PostgreSQL
"""


def _no_existing_result() -> Mock:
    """Simulates db_session.execute() finding no matching row."""
    result = Mock()
    result.scalars.return_value.first.return_value = None
    return result


def _existing_result() -> Mock:
    """Simulates db_session.execute() finding a matching row."""
    result = Mock()
    result.scalars.return_value.first.return_value = Mock()
    return result


@pytest.fixture
def pipeline() -> Any:
    pipeline = IngestionPipeline.__new__(IngestionPipeline)
    pipeline.vector_db = Mock()
    pipeline.embedding_provider = Mock()
    pipeline.embedding_provider.embed = Mock(return_value=[[0.1] * 1536])

    pipeline.db_session = Mock(spec=AsyncSession)
    pipeline.db_session.add = Mock()
    pipeline.db_session.commit = AsyncMock()

    pipeline.strategy_selector = Mock()
    pipeline.strategy_selector.chunk = Mock(return_value=[Mock(text="chunk 1", metadata={})])
    pipeline.batch_processor = Mock()
    pipeline.batch_processor.process = Mock(return_value=[])
    pipeline.resume_parser = Mock()
    pipeline.resume_parser.parse = Mock(
        return_value=Mock(
            text=SAMPLE_RESUME_MD,
            metadata={"detected_sections": ["experience", "skills"]},
        )
    )
    return pipeline


@pytest.mark.unit
class TestCheckSkip:
    """Isolated unit tests for IngestionPipeline._check_skip()."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_existing_source(self, pipeline: Any) -> None:
        pipeline.db_session.execute = AsyncMock(return_value=_no_existing_result())

        result = await pipeline._check_skip(
            source_id="resume_profile-999_abc123",
            profile_id="profile-999",
            content_hash="abc123",
            source_type="resume",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_skip_result_when_existing_source_found(self, pipeline: Any) -> None:
        pipeline.db_session.execute = AsyncMock(return_value=_existing_result())

        result = await pipeline._check_skip(
            source_id="resume_profile-999_abc123",
            profile_id="profile-999",
            content_hash="abc123",
            source_type="resume",
        )

        assert result is not None
        assert result.skipped is True
        assert result.chunk_count == 0
        assert result.skip_reason == "Source already ingested"


@pytest.mark.unit
class TestRecordIngestedSource:
    """Isolated unit test for IngestionPipeline._record_ingested_source()."""

    @pytest.mark.asyncio
    async def test_persists_new_row(self, pipeline: Any) -> None:
        await pipeline._record_ingested_source(
            source_id="resume_profile-999_abc123",
            source_type="resume",
            profile_id="profile-999",
            content_hash="abc123",
            chunk_count=3,
        )

        assert pipeline.db_session.add.call_count == 1
        added_record = pipeline.db_session.add.call_args[0][0]
        assert isinstance(added_record, IngestedSource)
        assert added_record.profile_id == "profile-999"
        assert added_record.source_type == "resume"
        assert added_record.content_hash == "abc123"
        assert added_record.chunk_count == 3

        assert pipeline.db_session.commit.call_count == 1


@pytest.mark.unit
class TestIngestResumeDedupBehavior:
    """Full-flow tests through ingest_resume(), covering PLAN.md's dedup cases."""

    @pytest.mark.asyncio
    async def test_changed_content_does_not_incorrectly_skip(self, pipeline: Any) -> None:
        # Neither call finds an existing row: first because it's genuinely
        # new, second because the content (and therefore hash) differs
        # from the first call.
        pipeline.db_session.execute = AsyncMock(
            side_effect=[_no_existing_result(), _no_existing_result()]
        )

        result_1 = await pipeline.ingest_resume(
            profile_id="profile-777",
            content=SAMPLE_RESUME_MD,
            filename="resume_v1.md",
        )
        result_2 = await pipeline.ingest_resume(
            profile_id="profile-777",
            content=SAMPLE_RESUME_MD + "\n\nUpdated skills: Rust, Go",
            filename="resume_v2.md",
        )

        assert result_1.skipped is False
        assert result_2.skipped is False
        assert (
            result_1.source_id != result_2.source_id
        ), "different content should hash differently, producing a distinct source_id"
        assert (
            pipeline.batch_processor.process.call_count == 2
        ), "both ingestions should proceed to embedding since the content differs"

    @pytest.mark.asyncio
    async def test_new_profile_with_no_prior_ingestions_proceeds(self, pipeline: Any) -> None:
        pipeline.db_session.execute = AsyncMock(return_value=_no_existing_result())

        result = await pipeline.ingest_resume(
            profile_id="profile-new",
            content=SAMPLE_RESUME_MD,
            filename="jane_doe_resume.md",
        )

        assert result.skipped is False
        assert result.chunk_count == 1
        assert (
            pipeline.db_session.commit.call_count == 1
        ), "a first-time ingestion should persist a new IngestedSource row"
