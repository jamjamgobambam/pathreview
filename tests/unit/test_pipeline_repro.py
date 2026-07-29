"""
Week 8 reproduction for issue #6: Duplicate embeddings generated when
re-ingesting the same repository.
https://github.com/ascherj/pathreview/issues/6

This test asserts the CORRECT behavior (identical content ingested twice
should skip the second time). It is expected to FAIL against the current
code on this branch -- that failure is the reproduction. It documents
exactly where the bug lives: ingestion/pipeline.py, _check_skip() and
_record_ingested_source(). Once issue #6 is fixed (Week 9), this test
should pass without modification.
"""

from typing import Any
from unittest.mock import Mock

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

    def test_reingesting_identical_content_should_skip(self, pipeline: Any) -> None:
        result_1 = pipeline.ingest_resume(
            profile_id="profile-123",
            content=SAMPLE_RESUME_MD,
            filename="jane_doe_resume.md",
        )
        result_2 = pipeline.ingest_resume(
            profile_id="profile-123",
            content=SAMPLE_RESUME_MD,
            filename="jane_doe_resume.md",
        )

        assert result_1.skipped is False, "first ingestion should proceed"
        assert result_2.skipped is True, (
            "BUG (issue #6): second identical ingestion should skip, but "
            "_check_skip() silently fails (AsyncSession has no .query()) "
            "and always returns None, so ingestion always proceeds."
        )
        assert pipeline.batch_processor.process.call_count == 1, (
            "BUG (issue #6): embeddings should only be generated once for "
            "identical content, but were generated on every call."
        )
