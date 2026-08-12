from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ingestion.pipeline import IngestionPipeline


@pytest.mark.integration
def test_resume_ingestion_pipeline_end_to_end() -> None:
    """Test complete resume ingestion from file to embedding storage."""

    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_resumes" / "sample_resume.md"

    resume_text = fixture_path.read_text()

    # Mock dependencies
    vector_db = Mock()
    db_session = Mock()

    embedding_provider = Mock()
    embedding_provider.embed.return_value = [[0.1] * 1536]

    # Create pipeline
    pipeline = IngestionPipeline(
        vector_db=vector_db,
        db_session=db_session,
        embedding_provider=embedding_provider,
    )

    # Mock pipeline methods
    with patch.object(pipeline, "_check_skip", return_value=None):
        with patch.object(pipeline, "_record_ingested_source") as mock_record:

            # Run ingestion
            result = pipeline.ingest_resume(
                profile_id="test-profile",
                content=resume_text,
                filename="sample_resume.md",
            )

            # Assertions
            assert result.skipped is False
            assert result.chunk_count > 0

            embedding_provider.embed.assert_called()
            vector_db.add.assert_called()
            mock_record.assert_called_once()
