"""Integration tests for ingestion deduplication functionality."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from ingestion.chunking.base import Chunk
from ingestion.pipeline import IngestionPipeline


@pytest.mark.integration
class TestIngestionDeduplication:
    """Integration tests for deduplication across multiple ingestions."""

    @pytest.fixture
    def mock_vector_db(self):
        """Create a mock vector database that tracks stored embeddings."""
        db = Mock()
        db.embeddings = []

        def mock_add(ids, embeddings, metadatas):
            for id_, emb, meta in zip(ids, embeddings, metadatas, strict=False):
                db.embeddings.append({"id": id_, "embedding": emb, "metadata": meta})

        db.add = Mock(side_effect=mock_add)
        db.get = Mock(return_value={"ids": [e["id"] for e in db.embeddings]})
        db.embeddings = []
        return db

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session that tracks ingested sources."""
        session = Mock()
        session.ingested_sources = []

        def mock_add(source):
            session.ingested_sources.append(source)
            session.add.reset_mock()  # Reset after adding

        session.add = Mock(side_effect=mock_add)
        session.commit = Mock()
        return session

    @pytest.fixture
    def mock_embedding_provider(self):
        """Create a mock embedding provider."""
        provider = Mock()
        provider.embed = Mock(return_value=[[0.1] * 1536, [0.2] * 1536, [0.3] * 1536])
        return provider

    @pytest.fixture
    def pipeline(self, mock_vector_db, mock_db_session, mock_embedding_provider):
        """Create an IngestionPipeline instance for integration testing."""
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
            p.batch_processor = Mock()
            p.batch_processor.process = Mock(return_value=[])
            return p

    # ==================== Deduplication Tests ====================

    def test_repo_deduplication_prevents_duplicate_embeddings(self, pipeline, mock_vector_db):
        """Re-ingesting same repo should not create duplicate embeddings."""
        repo_data = {"name": "test-repo", "description": "A test repository"}
        profile_id = str(uuid4())

        # Setup: Mock the repo analyzer to return consistent results
        parse_result = Mock()
        parse_result.text = "Repository content"
        parse_result.metadata = {"primary_language": "python"}
        pipeline.repo_analyzer.parse = Mock(return_value=parse_result)

        # Setup: Mock chunking
        chunks = [
            Chunk(text="Chunk 1", metadata={"source_id": "repo_test_hash"}),
            Chunk(text="Chunk 2", metadata={"source_id": "repo_test_hash"}),
        ]
        pipeline.strategy_selector.chunk = Mock(return_value=chunks)

        # Setup: Mock batch processor to actually store embeddings
        def mock_process(chunks_to_process):
            for i, chunk in enumerate(chunks_to_process):
                mock_vector_db.add(
                    ids=[f"{chunk.metadata['source_id']}_chunk_{i}"],
                    embeddings=[[0.1] * 1536],
                    metadatas=[chunk.metadata],
                )
            return [
                (c, f"{c.metadata['source_id']}_chunk_{i}") for i, c in enumerate(chunks_to_process)
            ]

        pipeline.batch_processor.process = Mock(side_effect=mock_process)

        # First ingestion
        result1 = pipeline.ingest_repo_metadata(profile_id=profile_id, repo_data=repo_data)
        embeddings_after_first = len(mock_vector_db.embeddings)

        assert result1.skipped is False
        assert embeddings_after_first == 2

        # Second ingestion with same data
        result2 = pipeline.ingest_repo_metadata(profile_id=profile_id, repo_data=repo_data)

        # Verify second ingestion was skipped
        assert result2.skipped is True
        assert len(mock_vector_db.embeddings) == embeddings_after_first  # No new embeddings

    def test_resume_deduplication_prevents_duplicate_embeddings(self, pipeline, mock_vector_db):
        """Re-ingesting same resume should not create duplicate embeddings."""
        resume_content = b"Jane Doe\nSoftware Engineer\nPython, JavaScript"
        profile_id = str(uuid4())

        # Setup: Mock parser
        parse_result = Mock()
        parse_result.text = "Parsed resume"
        parse_result.metadata = {"detected_sections": ["experience", "education"]}
        pipeline.resume_parser.parse = Mock(return_value=parse_result)

        # Setup: Mock chunking
        chunks = [
            Chunk(text="Resume chunk 1", metadata={"source_id": "resume_hash"}),
        ]
        pipeline.strategy_selector.chunk = Mock(return_value=chunks)

        # Setup: Mock batch processor
        def mock_process(chunks_to_process):
            for i, chunk in enumerate(chunks_to_process):
                mock_vector_db.add(
                    ids=[f"{chunk.metadata['source_id']}_chunk_{i}"],
                    embeddings=[[0.1] * 1536],
                    metadatas=[chunk.metadata],
                )
            return [
                (c, f"{c.metadata['source_id']}_chunk_{i}") for i, c in enumerate(chunks_to_process)
            ]

        pipeline.batch_processor.process = Mock(side_effect=mock_process)

        # First ingestion
        result1 = pipeline.ingest_resume(
            profile_id=profile_id, content=resume_content, filename="resume.pdf"
        )
        embeddings_after_first = len(mock_vector_db.embeddings)

        assert result1.skipped is False
        assert embeddings_after_first == 1

        # Second ingestion with identical content
        result2 = pipeline.ingest_resume(
            profile_id=profile_id, content=resume_content, filename="resume.pdf"
        )

        assert result2.skipped is True
        assert len(mock_vector_db.embeddings) == embeddings_after_first

    def test_different_profiles_both_ingest_same_repo(self, pipeline, mock_vector_db):
        """Same repo ingested by different profiles should create separate embeddings."""
        repo_data = {"name": "shared-repo", "description": "Shared repository"}
        profile_id_1 = str(uuid4())
        profile_id_2 = str(uuid4())

        # Setup: Mock repo analyzer
        parse_result = Mock()
        parse_result.text = "Repository content"
        parse_result.metadata = {"primary_language": "python"}
        pipeline.repo_analyzer.parse = Mock(return_value=parse_result)

        # Setup: Mock chunking
        chunks = [
            Chunk(text="Chunk 1", metadata={"source_id": "shared_repo_hash"}),
        ]
        pipeline.strategy_selector.chunk = Mock(return_value=chunks)

        # Setup: Mock batch processor
        def mock_process(chunks_to_process):
            for i, chunk in enumerate(chunks_to_process):
                mock_vector_db.add(
                    ids=[f"{chunk.metadata['source_id']}_chunk_{i}"],
                    embeddings=[[0.1] * 1536],
                    metadatas=[chunk.metadata],
                )
            return [
                (c, f"{c.metadata['source_id']}_chunk_{i}") for i, c in enumerate(chunks_to_process)
            ]

        pipeline.batch_processor.process = Mock(side_effect=mock_process)

        # User 1 ingests repo
        result1 = pipeline.ingest_repo_metadata(profile_id=profile_id_1, repo_data=repo_data)
        embeddings_after_user1 = len(mock_vector_db.embeddings)

        assert result1.skipped is False
        assert embeddings_after_user1 == 1

        # User 2 ingests same repo - should proceed (different profile)
        result2 = pipeline.ingest_repo_metadata(profile_id=profile_id_2, repo_data=repo_data)

        assert result2.skipped is False  # Should NOT be skipped for different profile
        assert len(mock_vector_db.embeddings) == embeddings_after_user1 + 1

    def test_different_source_types_with_same_content(self, pipeline, mock_vector_db):
        """Same content with different source_type should be ingested separately."""
        content = "# My Project\nPython FastAPI project"
        profile_id = str(uuid4())

        # Setup: Mock README parser
        parse_result_readme = Mock()
        parse_result_readme.text = content
        parse_result_readme.metadata = {"format": "markdown"}
        pipeline.readme_parser.parse = Mock(return_value=parse_result_readme)

        # Setup: Mock repo analyzer
        parse_result_repo = Mock()
        parse_result_repo.text = content
        parse_result_repo.metadata = {"primary_language": "python"}
        pipeline.repo_analyzer.parse = Mock(return_value=parse_result_repo)

        # Setup: Mock chunking
        chunks = [
            Chunk(text=content, metadata={"source_id": "content_hash"}),
        ]
        pipeline.strategy_selector.chunk = Mock(return_value=chunks)

        # Setup: Mock batch processor
        call_count = [0]

        def mock_process(chunks_to_process):
            call_count[0] += 1
            for i, chunk in enumerate(chunks_to_process):
                embedding_id = f"{chunk.metadata['source_id']}_chunk_{i}_call_{call_count[0]}"
                mock_vector_db.add(
                    ids=[embedding_id],
                    embeddings=[[0.1] * 1536],
                    metadatas=[chunk.metadata],
                )
            return [(c, f"id_{i}_{call_count[0]}") for i, c in enumerate(chunks_to_process)]

        pipeline.batch_processor.process = Mock(side_effect=mock_process)

        # Ingest as README
        result1 = pipeline.ingest_readme(
            profile_id=profile_id, content=content, repo_name="my-project"
        )
        embeddings_after_readme = len(mock_vector_db.embeddings)

        assert result1.skipped is False
        assert embeddings_after_readme == 1

        # Ingest same content as repo metadata - should NOT be skipped
        result2 = pipeline.ingest_repo_metadata(
            profile_id=profile_id, repo_data={"name": "my-project", "content": content}
        )

        assert result2.skipped is False  # Should NOT be skipped for different source_type
        assert len(mock_vector_db.embeddings) == embeddings_after_readme + 1

    def test_modified_content_creates_new_ingestion(self, pipeline, mock_vector_db):
        """Modified content should create a new ingestion, not skip."""
        profile_id = str(uuid4())

        # Setup: Mock parser
        parse_result = Mock()
        parse_result.text = "Original content"
        parse_result.metadata = {}
        pipeline.resume_parser.parse = Mock(return_value=parse_result)

        # Setup: Mock chunking
        chunks = [
            Chunk(text="Original chunk", metadata={"source_id": "original_hash"}),
        ]
        pipeline.strategy_selector.chunk = Mock(return_value=chunks)

        # Setup: Mock batch processor
        def mock_process(chunks_to_process):
            for i, chunk in enumerate(chunks_to_process):
                mock_vector_db.add(
                    ids=[f"{chunk.metadata['source_id']}_chunk_{i}"],
                    embeddings=[[0.1] * 1536],
                    metadatas=[chunk.metadata],
                )
            return [(c, f"id_{i}") for i, c in enumerate(chunks_to_process)]

        pipeline.batch_processor.process = Mock(side_effect=mock_process)

        # First ingestion with original content
        original_content = b"Original resume"
        result1 = pipeline.ingest_resume(
            profile_id=profile_id, content=original_content, filename="resume.pdf"
        )
        embeddings_after_first = len(mock_vector_db.embeddings)

        assert result1.skipped is False

        # Second ingestion with modified content (different hash)
        modified_content = b"Modified resume with new section"
        parse_result.text = "Modified content"
        chunks[0].metadata["source_id"] = "modified_hash"

        result2 = pipeline.ingest_resume(
            profile_id=profile_id, content=modified_content, filename="resume.pdf"
        )

        assert result2.skipped is False  # Should NOT be skipped because content is different
        assert len(mock_vector_db.embeddings) == embeddings_after_first + 1

    # ==================== Edge Case Tests ====================

    def test_concurrent_ingestions_of_same_source(self, pipeline, mock_vector_db):
        """Concurrent ingestions of the same source should handle gracefully."""
        repo_data = {"name": "test-repo"}
        profile_id = str(uuid4())

        # Setup mocks
        parse_result = Mock()
        parse_result.text = "Content"
        parse_result.metadata = {}
        pipeline.repo_analyzer.parse = Mock(return_value=parse_result)

        chunks = [Chunk(text="Chunk", metadata={"source_id": "hash"})]
        pipeline.strategy_selector.chunk = Mock(return_value=chunks)

        def mock_process(chunks_to_process):
            for i, chunk in enumerate(chunks_to_process):
                mock_vector_db.add(
                    ids=[f"{chunk.metadata['source_id']}_chunk_{i}"],
                    embeddings=[[0.1] * 1536],
                    metadatas=[chunk.metadata],
                )
            return [(c, f"id_{i}") for i, c in enumerate(chunks_to_process)]

        pipeline.batch_processor.process = Mock(side_effect=mock_process)

        # Simulate concurrent calls
        result1 = pipeline.ingest_repo_metadata(profile_id=profile_id, repo_data=repo_data)
        result2 = pipeline.ingest_repo_metadata(profile_id=profile_id, repo_data=repo_data)

        # First should succeed, second should be skipped
        assert result1.skipped is False
        assert result2.skipped is True
