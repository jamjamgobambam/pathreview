"""Tests for ingestion/pipeline.py"""

import hashlib
from unittest.mock import AsyncMock, Mock

import pytest

from core.models.ingested_source import IngestedSource
from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline

SAMPLE_README = "# My Project\n\nA short description of what this project does.\n"
SAMPLE_README_V2 = "# My Project\n\nAn updated description with new content.\n"
SAMPLE_RESUME = "# Jane Doe\n\n## Experience\n\nSoftware Engineer at Example Corp.\n"
SAMPLE_REPO_DATA = {"name": "my-repo", "language": "Python", "stars": 10}


@pytest.mark.unit
class TestIngestionPipeline:
    """Test suite for IngestionPipeline's hash-based skip behavior."""

    @pytest.fixture
    def mock_vector_db(self):
        return Mock()

    @pytest.fixture
    def mock_db_session(self):
        """Async DB session that reports no existing source by default."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()

        not_found = Mock()
        not_found.scalar_one_or_none = Mock(return_value=None)
        session.execute = AsyncMock(return_value=not_found)
        return session

    @pytest.fixture
    def pipeline(self, mock_vector_db, mock_db_session):
        return IngestionPipeline(
            vector_db=mock_vector_db,
            db_session=mock_db_session,
            embedding_provider=MockEmbeddingProvider(),
        )

    def _set_existing(self, mock_db_session, existing) -> None:
        """Configure mock_db_session.execute() to resolve to `existing`."""
        result = Mock()
        result.scalar_one_or_none = Mock(return_value=existing)
        mock_db_session.execute = AsyncMock(return_value=result)

    @pytest.mark.asyncio
    async def test_first_ingestion_embeds_and_records(
        self, pipeline, mock_vector_db, mock_db_session
    ):
        result = await pipeline.ingest_readme("profile-1", "my-repo", SAMPLE_README)

        assert result.skipped is False
        assert result.chunk_count > 0
        mock_vector_db.add.assert_called()

        mock_db_session.add.assert_called_once()
        recorded = mock_db_session.add.call_args[0][0]
        assert isinstance(recorded, IngestedSource)
        assert recorded.source_type == "readme"
        assert recorded.profile_id == "profile-1"
        assert recorded.filename == "my-repo"
        assert recorded.content_hash == hashlib.sha256(SAMPLE_README.encode()).hexdigest()
        mock_db_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_resubmitting_identical_content_skips(
        self, pipeline, mock_vector_db, mock_db_session
    ):
        self._set_existing(mock_db_session, existing=Mock())

        result = await pipeline.ingest_readme("profile-1", "my-repo", SAMPLE_README)

        assert result.skipped is True
        assert result.chunk_count == 0
        assert result.skip_reason == "Content unchanged since last ingestion"
        mock_vector_db.add.assert_not_called()
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_changed_content_produces_new_source_id_and_proceeds(
        self, pipeline, mock_db_session
    ):
        first = await pipeline.ingest_readme("profile-1", "my-repo", SAMPLE_README)
        second = await pipeline.ingest_readme("profile-1", "my-repo", SAMPLE_README_V2)

        assert first.skipped is False
        assert second.skipped is False
        assert first.source_id != second.source_id
        # Both versions get their own row; the old one is left untouched.
        assert mock_db_session.add.call_count == 2

    @pytest.mark.asyncio
    async def test_check_skip_degrades_gracefully_on_db_error(self, pipeline, mock_db_session):
        mock_db_session.execute = AsyncMock(side_effect=RuntimeError("db unavailable"))

        result = await pipeline._check_skip("readme_profile-1_my-repo_deadbeefdeadbeef")

        assert result is None

    @pytest.mark.asyncio
    async def test_ingest_resume_first_time_embeds(self, pipeline, mock_vector_db):
        result = await pipeline.ingest_resume("profile-1", SAMPLE_RESUME, "resume.md")

        assert result.skipped is False
        assert result.chunk_count > 0
        mock_vector_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_ingest_repo_metadata_first_time_embeds(self, pipeline, mock_vector_db):
        result = await pipeline.ingest_repo_metadata("profile-1", SAMPLE_REPO_DATA)

        assert result.skipped is False
        assert result.chunk_count > 0
        mock_vector_db.add.assert_called()

    def test_hash_content_returns_full_sha256_hexdigest(self, pipeline):
        content_hash = pipeline._hash_content(SAMPLE_README)

        assert content_hash == hashlib.sha256(SAMPLE_README.encode()).hexdigest()
        assert len(content_hash) == 64

    @pytest.mark.asyncio
    async def test_source_id_embeds_truncated_hash(self, pipeline):
        result = await pipeline.ingest_readme("profile-1", "my-repo", SAMPLE_README)

        full_hash = hashlib.sha256(SAMPLE_README.encode()).hexdigest()
        assert result.source_id == f"readme_profile-1_my-repo_{full_hash[:16]}"
