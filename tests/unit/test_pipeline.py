"""Tests for pipeline.py"""

from unittest.mock import Mock

import pytest

from ingestion.pipeline import IngestionPipeline


@pytest.mark.unit
class TestIngestionPipelineStaleEmbeddings:
    """Test suite for stale embedding removal during re-ingestion."""

    @pytest.fixture
    def mock_embedding_provider(self):
        """Create a mock embedding provider."""
        provider = Mock()
        provider.embed = Mock(side_effect=lambda texts: [[0.1] * 1536 for _ in texts])
        return provider

    @pytest.fixture
    def mock_vector_db(self):
        """Create a mock vector database collection."""
        return Mock()

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock DB session that reports no previously ingested source."""
        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        return session

    @pytest.fixture
    def pipeline(self, mock_vector_db, mock_db_session, mock_embedding_provider):
        """Create an IngestionPipeline instance."""
        return IngestionPipeline(mock_vector_db, mock_db_session, mock_embedding_provider)

    def _stored_metadatas(self, mock_vector_db) -> list[dict]:
        """Collect every metadata dict passed to the vector DB."""
        return [
            metadata
            for call in mock_vector_db.add.call_args_list
            for metadata in call.kwargs["metadatas"]
        ]

    def test_reingesting_updated_resume_deletes_previous_vectors(
        self, pipeline, mock_vector_db, sample_resume_text
    ):
        """Regression for #27: updated content must purge the previous embeddings."""
        updated_text = sample_resume_text.replace("2022-2024", "2022-2026")

        pipeline.ingest_resume("profile-1", sample_resume_text, "resume.md")
        mock_vector_db.reset_mock()

        pipeline.ingest_resume("profile-1", updated_text, "resume.md")

        mock_vector_db.delete.assert_called_once_with(
            where={"document_id": {"$eq": "resume_profile-1_resume.md"}}
        )

    def test_reingesting_updated_resume_leaves_only_new_vectors(
        self, pipeline, mock_vector_db, sample_resume_text
    ):
        """Regression for #27: the delete must precede the new chunk writes."""
        updated_text = sample_resume_text.replace("2022-2024", "2022-2026")

        pipeline.ingest_resume("profile-1", sample_resume_text, "resume.md")
        mock_vector_db.reset_mock()

        pipeline.ingest_resume("profile-1", updated_text, "resume.md")

        method_calls = [call[0] for call in mock_vector_db.method_calls]
        assert "delete" in method_calls
        assert "add" in method_calls
        assert method_calls.index("delete") < method_calls.index("add")

    def test_document_id_is_stable_across_content_changes(
        self, pipeline, mock_vector_db, sample_resume_text
    ):
        """Document ID must not change when content changes, unlike source ID."""
        updated_text = sample_resume_text.replace("2022-2024", "2022-2026")

        pipeline.ingest_resume("profile-1", sample_resume_text, "resume.md")
        first_metadatas = self._stored_metadatas(mock_vector_db)
        mock_vector_db.reset_mock()

        pipeline.ingest_resume("profile-1", updated_text, "resume.md")
        second_metadatas = self._stored_metadatas(mock_vector_db)

        assert first_metadatas[0]["document_id"] == second_metadatas[0]["document_id"]
        assert first_metadatas[0]["source_id"] != second_metadatas[0]["source_id"]

    def test_document_id_stored_on_every_chunk(self, pipeline, mock_vector_db, sample_resume_text):
        """Every stored chunk carries the document_id used for deletion."""
        pipeline.ingest_resume("profile-1", sample_resume_text, "resume.md")

        metadatas = self._stored_metadatas(mock_vector_db)
        assert metadatas
        assert all(m["document_id"] == "resume_profile-1_resume.md" for m in metadatas)

    def test_delete_is_scoped_to_the_ingested_document(
        self, pipeline, mock_vector_db, sample_resume_text
    ):
        """Ingesting one document must not delete another profile's vectors."""
        pipeline.ingest_resume("profile-1", sample_resume_text, "resume.md")
        pipeline.ingest_resume("profile-2", sample_resume_text, "resume.md")

        delete_filters = [call.kwargs["where"] for call in mock_vector_db.delete.call_args_list]
        assert delete_filters == [
            {"document_id": {"$eq": "resume_profile-1_resume.md"}},
            {"document_id": {"$eq": "resume_profile-2_resume.md"}},
        ]

    def test_first_ingestion_still_stores_chunks(
        self, pipeline, mock_vector_db, sample_resume_text
    ):
        """A no-op delete on first ingestion must not prevent storage."""
        result = pipeline.ingest_resume("profile-1", sample_resume_text, "resume.md")

        assert result.skipped is False
        assert result.chunk_count > 0
        assert mock_vector_db.add.called

    def test_unchanged_content_is_skipped_without_deleting(
        self, pipeline, mock_vector_db, mock_db_session, sample_resume_text
    ):
        """Re-ingesting unchanged content skips early and touches no vectors."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = Mock()

        result = pipeline.ingest_resume("profile-1", sample_resume_text, "resume.md")

        assert result.skipped is True
        mock_vector_db.delete.assert_not_called()
        mock_vector_db.add.assert_not_called()

    def test_reingesting_updated_readme_deletes_previous_vectors(
        self, pipeline, mock_vector_db, sample_readme_text
    ):
        """README re-ingestion purges the previous version's embeddings."""
        updated_text = sample_readme_text.replace("React 18", "React 19")

        pipeline.ingest_readme("profile-1", "weather-app", sample_readme_text)
        mock_vector_db.reset_mock()

        pipeline.ingest_readme("profile-1", "weather-app", updated_text)

        mock_vector_db.delete.assert_called_once_with(
            where={"document_id": {"$eq": "readme_profile-1_weather-app"}}
        )

    def test_reingesting_updated_repo_metadata_deletes_previous_vectors(
        self, pipeline, mock_vector_db
    ):
        """Repo metadata re-ingestion purges the previous version's embeddings."""
        repo_data = {"name": "weather-app", "language": "TypeScript", "stars": 3}

        pipeline.ingest_repo_metadata("profile-1", repo_data)
        mock_vector_db.reset_mock()

        pipeline.ingest_repo_metadata("profile-1", {**repo_data, "stars": 12})

        mock_vector_db.delete.assert_called_once_with(
            where={"document_id": {"$eq": "repo_profile-1_weather-app"}}
        )

    def test_delete_failure_prevents_storing_new_chunks(
        self, pipeline, mock_vector_db, sample_resume_text
    ):
        """A failed purge must abort ingestion rather than leave stale vectors."""
        mock_vector_db.delete = Mock(side_effect=RuntimeError("vector store unavailable"))

        with pytest.raises(RuntimeError):
            pipeline.ingest_resume("profile-1", sample_resume_text, "resume.md")

        mock_vector_db.add.assert_not_called()
