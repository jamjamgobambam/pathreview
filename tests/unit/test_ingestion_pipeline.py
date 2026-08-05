"""Tests for pipeline.py portfolio ingestion, metadata sanitization, and
stale-chunk cleanup."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from ingestion.pipeline import IngestionPipeline


@pytest.mark.unit
class TestSanitizeMetadata:
    """Test suite for IngestionPipeline._sanitize_metadata."""

    def test_drops_none_values(self):
        result = IngestionPipeline._sanitize_metadata({"title": None, "word_count": 5})
        assert "title" not in result
        assert result["word_count"] == 5

    def test_joins_list_values(self):
        result = IngestionPipeline._sanitize_metadata({"extracted_sections": ["about", "project"]})
        assert result["extracted_sections"] == "about,project"

    def test_joins_tuple_and_set_values(self):
        result = IngestionPipeline._sanitize_metadata({"a": ("x", "y"), "b": {"z"}})
        assert result["a"] == "x,y"
        assert result["b"] == "z"

    def test_preserves_scalars(self):
        result = IngestionPipeline._sanitize_metadata(
            {"title": "Jane Dev", "word_count": 10, "ratio": 0.5, "flag": True}
        )
        assert result == {"title": "Jane Dev", "word_count": 10, "ratio": 0.5, "flag": True}

    def test_stringifies_unknown_types(self):
        class Weird:
            def __str__(self):
                return "weird-value"

        result = IngestionPipeline._sanitize_metadata({"thing": Weird()})
        assert result["thing"] == "weird-value"

    def test_empty_list_becomes_empty_string(self):
        result = IngestionPipeline._sanitize_metadata({"extracted_sections": []})
        assert result["extracted_sections"] == ""


@pytest.mark.unit
class TestIngestPortfolio:
    """Test suite for IngestionPipeline.ingest_portfolio."""

    @pytest.fixture
    def mock_vector_db(self):
        db = MagicMock()
        return db

    @pytest.fixture
    def mock_embedding_provider(self):
        provider = Mock()
        provider.embed = Mock(return_value=[[0.1] * 1536])
        return provider

    @pytest.fixture
    def pipeline(self, mock_vector_db, mock_embedding_provider):
        db_session = Mock()
        db_session.query.side_effect = Exception("no db configured")
        return IngestionPipeline(
            vector_db=mock_vector_db,
            db_session=db_session,
            embedding_provider=mock_embedding_provider,
        )

    def test_deletes_existing_chunks_before_ingesting(self, pipeline, mock_vector_db):
        """A prior portfolio's chunks are removed before the new ones are stored."""
        html = "<html><body>Bio text here</body></html>"
        with patch("ingestion.pipeline.fetch_url", return_value=html):
            pipeline.ingest_portfolio(profile_id="p1", url="https://jane.dev")

        mock_vector_db.delete.assert_called_once()
        where_clause = mock_vector_db.delete.call_args.kwargs["where"]
        assert {"profile_id": "p1"} in where_clause["$and"]
        assert {"source_type": "portfolio"} in where_clause["$and"]

    def test_delete_failure_does_not_block_ingestion(self, pipeline, mock_vector_db):
        """If deleting stale chunks fails, ingestion still proceeds."""
        mock_vector_db.delete.side_effect = Exception("boom")

        html = "<html><body>Bio text here</body></html>"
        with patch("ingestion.pipeline.fetch_url", return_value=html):
            result = pipeline.ingest_portfolio(profile_id="p1", url="https://jane.dev")

        assert result.skipped is False
        assert result.chunk_count > 0

    def test_metadata_written_has_no_lists_or_none(self, pipeline, mock_vector_db):
        """Chunks stored in the vector DB never carry list or None metadata values."""
        html = (
            "<html><head><title>Jane</title></head>"
            "<body><h1>About</h1><p>Bio text here.</p></body></html>"
        )

        with patch("ingestion.pipeline.fetch_url", return_value=html):
            pipeline.ingest_portfolio(profile_id="p1", url="https://jane.dev")

        assert mock_vector_db.add.called
        for call in mock_vector_db.add.call_args_list:
            for metadata in call.kwargs["metadatas"]:
                for value in metadata.values():
                    assert not isinstance(value, (list, tuple, set))
                    assert value is not None

    def test_ingest_result_on_success(self, pipeline):
        html = "<html><body>Bio text here</body></html>"
        with patch("ingestion.pipeline.fetch_url", return_value=html):
            result = pipeline.ingest_portfolio(profile_id="p1", url="https://jane.dev")

        assert result.skipped is False
        assert result.chunk_count > 0
        assert result.source_id.startswith("portfolio_p1_")

    def test_fetch_failure_propagates(self, pipeline):
        """A fetch/parse failure raises rather than silently succeeding."""
        from ingestion.parsers.web_parser import WebParserError

        with (
            patch("ingestion.pipeline.fetch_url", side_effect=WebParserError("blocked")),
            pytest.raises(WebParserError),
        ):
            pipeline.ingest_portfolio(profile_id="p1", url="http://localhost")
