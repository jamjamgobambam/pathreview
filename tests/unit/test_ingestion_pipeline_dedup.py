"""Tests for shared dedup helpers in ingestion/pipeline.py"""

from unittest.mock import AsyncMock, Mock

import pytest

from core.models.ingested_source import IngestedSource
from ingestion.pipeline import IngestionPipeline


@pytest.mark.unit
class TestIngestionPipelineDedup:
    """Test suite for _check_skip and _record_ingested_source."""

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
    async def test_check_skip_returns_none_when_no_existing_source(self, pipeline, mock_db_session):
        """Test _check_skip returns None when no prior source is recorded."""
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await pipeline._check_skip(
            "readme_profile-123_my-repo_abcdef",
            "readme",
            "profile-123",
            "abcdef1234567890",
            filename="my-repo",
        )

        assert result is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_skip_skips_when_content_hash_matches(self, pipeline, mock_db_session):
        """Test _check_skip returns a skipped IngestResult when the stored hash matches."""
        existing_source = Mock()
        existing_source.content_hash = "abcdef1234567890"
        existing_source.chunk_count = 5

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = existing_source
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await pipeline._check_skip(
            "readme_profile-123_my-repo_abcdef",
            "readme",
            "profile-123",
            "abcdef1234567890",
            filename="my-repo",
        )

        assert result is not None
        assert result.skipped is True
        assert result.chunk_count == 5

    @pytest.mark.asyncio
    async def test_check_skip_does_not_skip_when_content_hash_differs(
        self, pipeline, mock_db_session
    ):
        """Test _check_skip returns None when stored content hash differs from incoming hash."""
        existing_source = Mock()
        existing_source.content_hash = "old_hash_1234567"
        existing_source.chunk_count = 5

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = existing_source
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await pipeline._check_skip(
            "readme_profile-123_my-repo_newhash",
            "readme",
            "profile-123",
            "new_hash_7654321",
            filename="my-repo",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_record_ingested_source_persists_to_db(self, pipeline, mock_db_session):
        """_record_ingested_source should add and commit an IngestedSource row."""
        content_hash = "abcdef1234567890"

        await pipeline._record_ingested_source(
            "readme_profile-123_my-repo_abcdef",
            "readme",
            "profile-123",
            3,
            content_hash=content_hash,
            source_url="my-repo",
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        recorded_source = mock_db_session.add.call_args[0][0]
        assert isinstance(recorded_source, IngestedSource)
        assert recorded_source.profile_id == "profile-123"
        assert recorded_source.source_type == "readme"
        assert recorded_source.content_hash == content_hash
        assert recorded_source.source_url == "my-repo"
        assert recorded_source.chunk_count == 3
