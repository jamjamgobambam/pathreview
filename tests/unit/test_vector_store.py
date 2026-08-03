"""Tests for vector_store.py"""

from unittest.mock import Mock

import pytest

from ingestion.chunking.base import Chunk
from rag.retriever.vector_store import VectorStore


@pytest.mark.unit
class TestVectorStoreAddChunks:
    """Test suite for VectorStore.add_chunks against the real Chunk contract."""

    @pytest.fixture
    def collection(self):
        """Create a stand-in ChromaDB collection."""
        return Mock()

    @pytest.fixture
    def store(self, collection):
        """Create a VectorStore whose client is never constructed."""
        store = VectorStore.__new__(VectorStore)
        store.client = Mock()
        store.get_collection = Mock(return_value=collection)
        return store

    @pytest.fixture
    def chunks(self):
        """Create Chunk objects shaped the way the chunkers emit them."""
        return [
            Chunk(
                text="Built REST APIs using Python and FastAPI",
                metadata={
                    "source_id": "resume_bench01",
                    "source_type": "resume",
                    "chunk_index": 0,
                    "char_start": 0,
                    "char_end": 40,
                },
            ),
            Chunk(
                text="Weather forecasting app built with React",
                metadata={
                    "source_id": "readme_bench01",
                    "source_type": "readme",
                    "chunk_index": 1,
                    "heading_path": "Weather App > Tech Stack",
                },
            ),
        ]

    def test_real_chunk_objects_are_indexed(self, store, collection, chunks):
        """Test add_chunks accepts the two-field Chunk dataclass without AttributeError."""
        embeddings = [[0.1] * 4, [0.2] * 4]

        store.add_chunks(list(zip(chunks, embeddings, strict=True)), "profile_bench01")

        collection.upsert.assert_called_once()

    def test_ids_follow_batch_processor_convention(self, store, collection, chunks):
        """Test derived ids match BatchEmbeddingProcessor's {source_id}_chunk_{index} format."""
        store.add_chunks(list(zip(chunks, [[0.1] * 4, [0.2] * 4], strict=True)), "profile_bench01")

        kwargs = collection.upsert.call_args.kwargs
        assert kwargs["ids"] == ["resume_bench01_chunk_0", "readme_bench01_chunk_1"]

    def test_documents_and_embeddings_are_paired(self, store, collection, chunks):
        """Test each stored document keeps its own embedding and text."""
        embeddings = [[0.1] * 4, [0.2] * 4]

        store.add_chunks(list(zip(chunks, embeddings, strict=True)), "profile_bench01")

        kwargs = collection.upsert.call_args.kwargs
        assert kwargs["documents"] == [chunks[0].text, chunks[1].text]
        assert kwargs["embeddings"] == embeddings

    def test_metadata_is_read_from_chunk_metadata(self, store, collection, chunks):
        """Test source_id and chunk_index come from metadata, not from attributes."""
        store.add_chunks(list(zip(chunks, [[0.1] * 4, [0.2] * 4], strict=True)), "profile_bench01")

        kwargs = collection.upsert.call_args.kwargs
        assert kwargs["metadatas"][0]["source_id"] == "resume_bench01"
        assert kwargs["metadatas"][0]["chunk_index"] == 0
        assert kwargs["metadatas"][1]["source_id"] == "readme_bench01"
        assert kwargs["metadatas"][1]["chunk_index"] == 1

    def test_section_defaults_to_empty_string(self, store, collection, chunks):
        """Test the optional section field is stored as '' when absent."""
        store.add_chunks(list(zip(chunks, [[0.1] * 4, [0.2] * 4], strict=True)), "profile_bench01")

        kwargs = collection.upsert.call_args.kwargs
        assert all(metadata["section"] == "" for metadata in kwargs["metadatas"])

    def test_section_is_preserved_when_present(self, store, collection):
        """Test a section supplied in metadata reaches the stored record."""
        chunk = Chunk(
            text="Experience",
            metadata={"source_id": "resume_x", "chunk_index": 0, "section": "experience"},
        )

        store.add_chunks([(chunk, [0.1] * 4)], "profile_x")

        kwargs = collection.upsert.call_args.kwargs
        assert kwargs["metadatas"][0]["section"] == "experience"

    def test_missing_metadata_keys_fall_back(self, store, collection):
        """Test a chunk without source_id or chunk_index is still indexable."""
        chunk = Chunk(text="Orphan chunk", metadata={})

        store.add_chunks([(chunk, [0.1] * 4)], "profile_x")

        kwargs = collection.upsert.call_args.kwargs
        assert kwargs["ids"] == ["unknown_chunk_0"]

    def test_empty_input_does_not_call_upsert(self, store, collection):
        """Test an empty chunk list is a no-op rather than an empty upsert."""
        store.add_chunks([], "profile_bench01")

        collection.upsert.assert_not_called()

    def test_stored_metadata_values_are_chroma_compatible(self, store, collection, chunks):
        """Test stored metadata contains only scalar types ChromaDB accepts."""
        store.add_chunks(list(zip(chunks, [[0.1] * 4, [0.2] * 4], strict=True)), "profile_bench01")

        kwargs = collection.upsert.call_args.kwargs
        for metadata in kwargs["metadatas"]:
            assert all(isinstance(v, (str, int, float, bool)) for v in metadata.values())
