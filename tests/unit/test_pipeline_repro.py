"""
Week 8 reproduction for issue #6: Duplicate embeddings generated when
re-ingesting the same repository.
https://github.com/ascherj/pathreview/issues/6

This test originally asserted the CORRECT behavior (identical content
ingested twice should skip the second time) and was expected to FAIL
against the pre-fix code -- that failure was the Week 8 reproduction.

Week 9 update: ingestion/pipeline.py has been fixed (_check_skip() and
_record_ingested_source() now use the real async ORM API instead of the
broken sync .query() call). The pipeline methods are now async, so this
test has been updated to await them and to mock db_session.execute()
instead of db_session.query(). The assertions are otherwise unchanged
from the Week 8 version. This test now passes.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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


@pytest.mark.unit
class TestIngestionPipelineDuplicateReingestion:
    """Reproduction for issue #6."""

    @pytest.fixture
    def pipeline(self) -> Any:
        pipeline = IngestionPipeline.__new__(IngestionPipeline)
        pipeline.vector_db = Mock()
        pipeline.embedding_provider = Mock()
        pipeline.embedding_provider.embed = Mock(return_value=[[0.1] * 1536])

        pipeline.db_session = Mock(spec=AsyncSession)

        # First _check_skip() call: no existing row found -> proceed.
        no_existing_result = Mock()
        no_existing_result.scalars.return_value.first.return_value = None

        # Second _check_skip() call: existing row found -> skip.
        existing_result = Mock()
        existing_result.scalars.return_value.first.return_value = Mock()

        pipeline.db_session.execute = AsyncMock(side_effect=[no_existing_result, existing_result])
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

    @pytest.mark.asyncio
    async def test_reingesting_identical_content_should_skip(self, pipeline: Any) -> None:
        result_1 = await pipeline.ingest_resume(
            profile_id="profile-123",
            content=SAMPLE_RESUME_MD,
            filename="jane_doe_resume.md",
        )
        result_2 = await pipeline.ingest_resume(
            profile_id="profile-123",
            content=SAMPLE_RESUME_MD,
            filename="jane_doe_resume.md",
        )

        assert result_1.skipped is False, "first ingestion should proceed"
        assert result_2.skipped is True, (
            "second identical ingestion should skip: _check_skip() should "
            "find the row recorded by the first call and return early."
        )
        assert pipeline.batch_processor.process.call_count == 1, (
            "embeddings should only be generated once for identical " "content, not on every call."
        )
        assert pipeline.db_session.commit.call_count == 1, (
            "the database record should only be committed once, on the "
            "first (non-skipped) ingestion."
        )
