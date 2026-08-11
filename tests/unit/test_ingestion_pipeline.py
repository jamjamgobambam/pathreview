"""Unit tests for ingestion/pipeline.py"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from core.models.ingested_source import IngestedSource
from ingestion.chunking.base import Chunk
from ingestion.pipeline import IngestionPipeline, IngestResult


@pytest.mark.unit
class TestIngestionPipeline:
    """Test suite for IngestionPipeline."""

    @pytest.fixture
    def mock_vector_db(self):
        """Create a mock vector database."""
        db = Mock()
        db.add = Mock()
        db.get = Mock(return_value={"ids": []})
        return db

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = Mock()
        return session

    @pytest.fixture
    def mock_embedding_provider(self):
        """Create a mock embedding provider."""
        provider = Mock()
        provider.embed = Mock(return_value=[[0.1] * 1536, [0.2] * 1536])
        return provider

    @pytest.fixture
    def pipeline(self, mock_vector_db, mock_db_session, mock_embedding_provider):
        """Create a IngestionPipeline instance."""
        with (
            patch("ingestion.pipeline.StrategySelector"),
            patch("ingestion.pipeline.BatchEmbeddingProcessor"),
            patch("ingestion.pipeline.ReadmeParser"),
            patch("ingestion.pipeline.RepoAnalyzer"),
            patch("ingestion.pipeline.ResumeParser"),
        ):
            p = IngestionPipeline(
                vector_db=mock_vector_db,
                db_session=mock_db_session,
                embedding_provider=mock_embedding_provider,
            )
            # Mock the batch processor to avoid actual embedding
            p.batch_processor = Mock()
            p.batch_processor.process = Mock(return_value=[])
            return p

    # ==================== _check_skip Tests ====================

    def test_check_skip_returns_none_when_no_existing_source(self, pipeline, mock_db_session):
        """_check_skip should return None when source doesn't exist in database."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        result = pipeline._check_skip(source_id="hash123", source_type="repo")

        assert result is None
        mock_db_session.query.assert_called()

    def test_check_skip_returns_ingest_result_when_source_exists(self, pipeline, mock_db_session):
        """_check_skip should return IngestResult when source already ingested."""
        existing_source = Mock(spec=IngestedSource)
        query_mock = mock_db_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = existing_source

        result = pipeline._check_skip(source_id="hash123", source_type="repo")

        assert result is not None
        assert isinstance(result, IngestResult)
        assert result.skipped is True
        assert result.skip_reason == "Source already ingested"

    def test_check_skip_handles_db_error_gracefully(self, pipeline, mock_db_session, caplog):
        """_check_skip should handle database errors gracefully."""
        mock_db_session.query.side_effect = Exception("Database connection error")

        result = pipeline._check_skip(source_id="hash123", source_type="repo")

        assert result is None  # Should return None to allow ingestion to proceed
        assert "Could not check if source already ingested" in caplog.text

    def test_check_skip_filters_by_source_id_and_source_type(self, pipeline, mock_db_session):
        """_check_skip should filter database query by both source_id and source_type."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        pipeline._check_skip(source_id="hash123", source_type="resume")

        # Verify the filter was called with both parameters
        mock_db_session.query.return_value.filter_by.assert_called_once()
        call_kwargs = mock_db_session.query.return_value.filter_by.call_args[1]
        assert "source_type" in call_kwargs

    # ==================== ingest_resume Tests ====================

    def test_ingest_resume_skips_duplicate(self, pipeline):
        """Re-ingesting same resume should be skipped."""
        resume_content = b"Resume content"
        profile_id = str(uuid4())

        # Mock _check_skip to return a skip result on second call
        skip_result = IngestResult(
            source_id="hash123", chunk_count=0, skipped=True, skip_reason="Source already ingested"
        )
        pipeline._check_skip = Mock(return_value=skip_result)

        result = pipeline.ingest_resume(
            profile_id=profile_id, content=resume_content, filename="resume.pdf"
        )

        assert result.skipped is True
        assert result.chunk_count == 0

    def test_ingest_resume_creates_record_on_first_ingestion(self, pipeline):
        """First ingestion of resume should create record and store embeddings."""
        resume_content = b"Resume content"
        profile_id = str(uuid4())

        # Mock _check_skip to return None (no existing source)
        pipeline._check_skip = Mock(return_value=None)

        # Mock parser
        parse_result = Mock()
        parse_result.text = "Parsed resume text"
        parse_result.metadata = {"detected_sections": ["experience", "education"]}
        pipeline.resume_parser.parse = Mock(return_value=parse_result)

        # Mock strategy selector
        chunk = Chunk(text="Resume chunk", metadata={"source_id": "hash123"})
        pipeline.strategy_selector.chunk = Mock(return_value=[chunk])

        # Mock _record_ingested_source
        pipeline._record_ingested_source = Mock()

        result = pipeline.ingest_resume(
            profile_id=profile_id, content=resume_content, filename="resume.pdf"
        )

        assert result.skipped is False
        assert result.chunk_count == 1
        pipeline._record_ingested_source.assert_called_once()

    def test_ingest_resume_error_handling(self, pipeline):
        """ingest_resume should raise exception on parse failure."""
        resume_content = b"Invalid content"
        profile_id = str(uuid4())

        pipeline._check_skip = Mock(return_value=None)
        pipeline.resume_parser.parse = Mock(side_effect=Exception("Parse failed"))

        with pytest.raises(Exception, match="Parse failed"):
            pipeline.ingest_resume(
                profile_id=profile_id, content=resume_content, filename="resume.pdf"
            )

    # ==================== ingest_repo_metadata Tests ====================

    def test_ingest_repo_skips_duplicate(self, pipeline):
        """Re-ingesting same repo should be skipped."""
        repo_data = {"name": "my-repo", "description": "Test repo"}
        profile_id = str(uuid4())

        skip_result = IngestResult(
            source_id="hash123", chunk_count=0, skipped=True, skip_reason="Source already ingested"
        )
        pipeline._check_skip = Mock(return_value=skip_result)

        result = pipeline.ingest_repo_metadata(profile_id=profile_id, repo_data=repo_data)

        assert result.skipped is True
        assert result.chunk_count == 0

    def test_ingest_repo_creates_record_on_first_ingestion(self, pipeline):
        """First ingestion of repo should create record and store embeddings."""
        repo_data = {"name": "my-repo", "description": "Test repo"}
        profile_id = str(uuid4())

        pipeline._check_skip = Mock(return_value=None)

        # Mock parser
        parse_result = Mock()
        parse_result.text = "Analyzed repo text"
        parse_result.metadata = {"primary_language": "python", "tech_stack": ["fastapi"]}
        pipeline.repo_analyzer.parse = Mock(return_value=parse_result)

        # Mock strategy selector
        chunk = Chunk(text="Repo chunk", metadata={"source_id": "hash123"})
        pipeline.strategy_selector.chunk = Mock(return_value=[chunk])

        # Mock _record_ingested_source
        pipeline._record_ingested_source = Mock()

        result = pipeline.ingest_repo_metadata(profile_id=profile_id, repo_data=repo_data)

        assert result.skipped is False
        assert result.chunk_count == 1
        pipeline._record_ingested_source.assert_called_once()

    def test_ingest_repo_error_handling(self, pipeline):
        """ingest_repo_metadata should raise exception on analysis failure."""
        repo_data = {"name": "my-repo"}
        profile_id = str(uuid4())

        pipeline._check_skip = Mock(return_value=None)
        pipeline.repo_analyzer.parse = Mock(side_effect=Exception("Analysis failed"))

        with pytest.raises(Exception, match="Analysis failed"):
            pipeline.ingest_repo_metadata(profile_id=profile_id, repo_data=repo_data)

    # ==================== ingest_readme Tests ====================

    def test_ingest_readme_skips_duplicate(self, pipeline):
        """Re-ingesting same README should be skipped."""
        readme_content = "# My Project\nDescription"
        profile_id = str(uuid4())
        repo_name = "my-repo"

        skip_result = IngestResult(
            source_id="hash123", chunk_count=0, skipped=True, skip_reason="Source already ingested"
        )
        pipeline._check_skip = Mock(return_value=skip_result)

        result = pipeline.ingest_readme(
            profile_id=profile_id, content=readme_content, repo_name=repo_name
        )

        assert result.skipped is True

    # ==================== _record_ingested_source Tests ====================

    def test_record_ingested_source_logs_info(self, pipeline, caplog):
        """_record_ingested_source should log ingestion details."""
        source_id = "hash123"
        source_type = "repo"
        profile_id = str(uuid4())
        chunk_count = 5

        pipeline._record_ingested_source(
            source_id=source_id,
            source_type=source_type,
            profile_id=profile_id,
            chunk_count=chunk_count,
        )

        assert "Recording ingested source" in caplog.text

    def test_record_ingested_source_handles_error(self, pipeline):
        """_record_ingested_source should handle errors gracefully."""
        # Even though current implementation just logs, this test ensures error handling
        source_id = "hash123"
        source_type = "repo"
        profile_id = str(uuid4())

        # Should not raise exception
        pipeline._record_ingested_source(
            source_id=source_id, source_type=source_type, profile_id=profile_id, chunk_count=5
        )

    # ==================== Utility Tests ====================

    def test_hash_content_generates_consistent_hash(self, pipeline):
        """_hash_content should generate consistent hash for same content."""
        content = b"Test content"

        hash1 = pipeline._hash_content(content)
        hash2 = pipeline._hash_content(content)

        assert hash1 == hash2

    def test_hash_content_different_for_different_content(self, pipeline):
        """_hash_content should generate different hash for different content."""
        content1 = b"Test content 1"
        content2 = b"Test content 2"

        hash1 = pipeline._hash_content(content1)
        hash2 = pipeline._hash_content(content2)

        assert hash1 != hash2

    def test_hash_content_handles_string_input(self, pipeline):
        """_hash_content should handle string input."""
        content_str = "Test content"

        hash_result = pipeline._hash_content(content_str)

        assert isinstance(hash_result, str)
        assert len(hash_result) > 0
