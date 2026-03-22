"""Tests for batch_processor.py"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from ingestion.chunking.base import Chunk
from ingestion.embeddings.batch_processor import BatchEmbeddingProcessor


@pytest.mark.unit
class TestBatchEmbeddingProcessor:
    """Test suite for BatchEmbeddingProcessor."""

    @pytest.fixture
    def mock_embedding_provider(self):
        """Create a mock embedding provider."""
        provider = Mock()
        provider.embed = Mock(return_value=[
            [0.1] * 1536,
            [0.2] * 1536,
            [0.3] * 1536,
        ])
        return provider

    @pytest.fixture
    def mock_vector_db(self):
        """Create a mock vector database."""
        db = Mock()
        return db

    @pytest.fixture
    def processor(self, mock_embedding_provider, mock_vector_db):
        """Create a BatchEmbeddingProcessor instance."""
        return BatchEmbeddingProcessor(mock_embedding_provider, mock_vector_db)

    def test_empty_chunks_list_returns_empty(self, processor, caplog):
        """Test that empty chunks list logs warning and returns empty list."""
        result = processor.process([])

        assert result == []
        # Should log a warning
        assert "Empty chunks list" in caplog.text or any(
            "empty" in record.message.lower() for record in caplog.records
        )

    def test_normal_chunks_list_processes(self, processor, mock_embedding_provider):
        """Test processing normal chunks list."""
        chunks = [
            Chunk(text="First chunk", metadata={"id": 1}),
            Chunk(text="Second chunk", metadata={"id": 2}),
            Chunk(text="Third chunk", metadata={"id": 3}),
        ]

        # Mock the _store_embedding method
        processor._store_embedding = Mock(side_effect=["id1", "id2", "id3"])

        result = processor.process(chunks)

        assert len(result) == 3
        assert all(isinstance(r, tuple) for r in result)
        mock_embedding_provider.embed.assert_called()

    def test_batches_chunks_correctly(self, processor):
        """Test that chunks are batched correctly."""
        # Create more chunks than the batch size
        chunks = [
            Chunk(text=f"Chunk {i}", metadata={"id": i})
            for i in range(250)
        ]

        processor._store_embedding = Mock(side_effect=[f"id{i}" for i in range(250)])

        with patch.object(processor.embedding_provider, 'embed') as mock_embed:
            mock_embed.return_value = [[0.1] * 1536 for _ in range(len(chunks))]

            result = processor.process(chunks)

            # Should process in multiple batches
            # Default BATCH_SIZE is 100, so 250 chunks = 3 batches
            assert mock_embed.call_count >= 2
            assert len(result) == 250

    def test_returns_chunk_and_embedding_id_tuples(self, processor, mock_embedding_provider):
        """Test that return value is list of (chunk, embedding_id) tuples."""
        chunks = [
            Chunk(text="Test chunk", metadata={"source": "test"}),
        ]

        processor._store_embedding = Mock(return_value="embedding_123")

        result = processor.process(chunks)

        assert len(result) == 1
        chunk_result, embedding_id = result[0]
        assert isinstance(chunk_result, Chunk)
        assert chunk_result.text == "Test chunk"
        assert embedding_id == "embedding_123"

    def test_embedding_provider_called_with_texts(self, processor, mock_embedding_provider):
        """Test that embedding provider is called with chunk texts."""
        chunks = [
            Chunk(text="First", metadata={}),
            Chunk(text="Second", metadata={}),
        ]

        processor._store_embedding = Mock(side_effect=["id1", "id2"])

        result = processor.process(chunks)

        # Check that embed was called with the texts
        mock_embedding_provider.embed.assert_called()
        call_args = mock_embedding_provider.embed.call_args
        assert call_args[0][0] == ["First", "Second"]

    def test_chunk_metadata_preserved(self, processor):
        """Test that chunk metadata is preserved in results."""
        original_metadata = {"source": "readme", "index": 5, "heading": "Installation"}
        chunks = [
            Chunk(text="Test", metadata=original_metadata),
        ]

        processor._store_embedding = Mock(return_value="id123")

        result = processor.process(chunks)

        returned_chunk, _ = result[0]
        assert returned_chunk.metadata["source"] == "readme"
        assert returned_chunk.metadata["index"] == 5
        assert returned_chunk.metadata["heading"] == "Installation"

    def test_batch_size_limit(self, processor):
        """Test that batches respect BATCH_SIZE limit."""
        # Create exactly BATCH_SIZE + 1 chunks
        chunk_count = processor.BATCH_SIZE + 1
        chunks = [Chunk(text=f"Chunk {i}", metadata={}) for i in range(chunk_count)]

        processor._store_embedding = Mock(side_effect=[f"id{i}" for i in range(chunk_count)])

        with patch.object(processor.embedding_provider, 'embed') as mock_embed:
            mock_embed.return_value = [[0.1] * 1536 for _ in range(chunk_count)]

            processor.process(chunks)

            # Should be called at least twice (one full batch + remainder)
            assert mock_embed.call_count >= 2
            # First call should have BATCH_SIZE items
            first_call_args = mock_embed.call_args_list[0][0][0]
            assert len(first_call_args) == processor.BATCH_SIZE

    def test_many_chunks(self, processor):
        """Test processing a large number of chunks."""
        chunks = [Chunk(text=f"Chunk {i}", metadata={"id": i}) for i in range(500)]

        processor._store_embedding = Mock(side_effect=[f"id{i}" for i in range(500)])

        with patch.object(processor.embedding_provider, 'embed') as mock_embed:
            mock_embed.return_value = [[0.1] * 1536 for _ in range(500)]

            result = processor.process(chunks)

            assert len(result) == 500
            # Should be processed in multiple batches
            assert mock_embed.call_count >= 2

    def test_embedding_provider_exception_propagates(self, processor):
        """Test that exception from embedding provider is raised."""
        chunks = [Chunk(text="Test", metadata={})]

        processor.embedding_provider.embed = Mock(side_effect=RuntimeError("API Error"))

        with pytest.raises(RuntimeError):
            processor.process(chunks)

    def test_store_embedding_called_for_each_chunk(self, processor):
        """Test that _store_embedding is called for each chunk."""
        chunks = [
            Chunk(text=f"Chunk {i}", metadata={})
            for i in range(5)
        ]

        processor._store_embedding = Mock(side_effect=[f"id{i}" for i in range(5)])

        with patch.object(processor.embedding_provider, 'embed') as mock_embed:
            mock_embed.return_value = [[0.1] * 1536 for _ in range(5)]

            processor.process(chunks)

            # _store_embedding should be called once per chunk
            assert processor._store_embedding.call_count == 5

    def test_chunk_text_extraction(self, processor):
        """Test that text is correctly extracted from chunks for embedding."""
        chunks = [
            Chunk(text="Important content here", metadata={"id": 1}),
            Chunk(text="More important content", metadata={"id": 2}),
        ]

        processor._store_embedding = Mock(side_effect=["id1", "id2"])

        with patch.object(processor.embedding_provider, 'embed') as mock_embed:
            mock_embed.return_value = [[0.1] * 1536, [0.2] * 1536]

            processor.process(chunks)

            # Verify texts were extracted correctly
            called_texts = mock_embed.call_args[0][0]
            assert called_texts[0] == "Important content here"
            assert called_texts[1] == "More important content"
