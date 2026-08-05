"""Tests reproducing missing content-hash-based skip detection in ingestion pipeline."""

from unittest.mock import AsyncMock, Mock

import pytest

from ingestion.pipeline import IngestionPipeline


@pytest.mark.unit
class TestUnchangedDocumentDetection:
    """Reproduction suite for issue: re-embedding unchanged documents."""

    @pytest.fixture
    def mock_vector_db(self):
        """Create a mock vector database."""
        return Mock()

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_embedding_provider(self):
        """Create a mock embedding provider."""
        provider = Mock()
        provider.embed = Mock(return_value=[[0.1] * 1536])
        return provider

    @pytest.fixture
    def pipeline(self, mock_vector_db, mock_db_session, mock_embedding_provider):
        """Create an IngestionPipeline instance with mocked dependencies."""
        pipeline = IngestionPipeline(
            vector_db=mock_vector_db,
            db_session=mock_db_session,
            embedding_provider=mock_embedding_provider,
        )
        pipeline.batch_processor.process = Mock(return_value=[])
        return pipeline

    @pytest.mark.asyncio
    async def test_reingesting_unchanged_readme_is_skipped(self, pipeline, mock_db_session):
        """Re-submitting the exact same README content should skip re-embedding."""
        profile_id = "profile-123"
        repo_name = "my-repo"
        content = "# Hello World\nSame content every time"

        no_existing_result = Mock()
        no_existing_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=no_existing_result)

        first_result = await pipeline.ingest_readme(profile_id, repo_name, content)

        existing_source = Mock()
        existing_source.content_hash = pipeline._hash_content(content)
        existing_source.chunk_count = first_result.chunk_count
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = existing_source
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        second_result = await pipeline.ingest_readme(profile_id, repo_name, content)

        assert first_result.skipped is False
        assert second_result.skipped is True

    @pytest.mark.asyncio
    async def test_reingesting_unchanged_readme_calls_batch_processor_once(
        self, pipeline, mock_db_session
    ):
        """Unchanged README content should only trigger embedding generation once."""
        profile_id = "profile-123"
        repo_name = "my-repo"
        content = "# Hello World\nSame content every time"

        no_existing_result = Mock()
        no_existing_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=no_existing_result)

        await pipeline.ingest_readme(profile_id, repo_name, content)

        existing_source = Mock()
        existing_source.content_hash = pipeline._hash_content(content)
        existing_source.chunk_count = 0
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = existing_source
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await pipeline.ingest_readme(profile_id, repo_name, content)

        assert pipeline.batch_processor.process.call_count == 1
