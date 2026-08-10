"""Covers issue #80: deleting a profile left its ChromaDB embeddings
orphaned, because delete_profile() never touched the vector store.

Tests whether delete_profile() drops the profile's ChromaDB collection
via VectorStore.delete_collection(). This tests seed a ChromaDB
collection with an embedding tied to a profile's ingested source, run
delete_profile() against a mocked DB session, and assert the collection
is gone afterward. VectorStore is patched so delete_profile()'s internal
VectorStore() call resolves to the same temp-backed instance the test seeded.
"""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from core.services.profile_service import delete_profile
from rag.retriever.vector_store import VectorStore


class FakeChunk:
    def __init__(
        self,
        id: str,
        source_id: str,
        text: str,
        chunk_index: int = 0,
        section: str | None = None,
    ) -> None:
        self.id = id
        self.source_id = source_id
        self.text = text
        self.chunk_index = chunk_index
        self.section = section


@pytest.mark.unit
class TestProfileDeleteVectorCleanup:

    @pytest.fixture
    def vector_store(self, tmp_path: Path) -> VectorStore:
        return VectorStore(persist_dir=str(tmp_path / "chromadb"))

    @staticmethod
    def _mock_db(sources: list[Any]) -> AsyncMock:
        mock_db = AsyncMock()

        review_result = Mock()
        review_result.scalars.return_value.all.return_value = []

        source_result = Mock()
        source_result.scalars.return_value.all.return_value = sources

        mock_db.execute = AsyncMock(side_effect=[review_result, source_result])
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()
        return mock_db

    @pytest.mark.asyncio
    async def test_delete_profile_purges_embeddings(self, vector_store: VectorStore) -> None:
        """delete_profile() removes the profile's ChromaDB collection
        entirely (not just its documents) when it has one ingested source
        with embeddings — the core issue #80 fix, verified end-to-end
        against a real (tmp-dir-backed) ChromaDB instance."""
        profile_id = uuid4()
        user_id = uuid4()
        source_id = str(uuid4())
        collection_name = f"profile_{profile_id}"

        # Seed the vector store the way ingestion would: one embedded chunk
        # belonging to this profile's ingested source.
        chunk = FakeChunk(id=str(uuid4()), source_id=source_id, text="Experienced Python engineer")
        vector_store.add_chunks([(chunk, [0.1, 0.2, 0.3])], collection_name)

        # Sanity check the embedding actually exists before deletion.
        assert vector_store.get_collection(collection_name).count() == 1

        fake_profile = Mock(id=profile_id, user_id=user_id)
        fake_source = Mock(id=source_id, profile_id=profile_id)
        mock_db = self._mock_db([fake_source])

        async def fake_get_profile(db: Any, pid: UUID, uid: UUID) -> Mock:
            return fake_profile

        with (
            patch("core.services.profile_service.get_profile", fake_get_profile),
            patch("core.services.profile_service.VectorStore", return_value=vector_store),
        ):
            deleted = await delete_profile(mock_db, profile_id, user_id)

        assert deleted is True

        # The collection itself should be gone, not just emptied.
        remaining_collections = [c.name for c in vector_store.client.list_collections()]
        assert collection_name not in remaining_collections, (
            f"Expected delete_profile() to remove the '{collection_name}' ChromaDB "
            f"collection, but it still exists."
        )

    @pytest.mark.asyncio
    async def test_delete_profile_purges_embeddings_from_multiple_sources(
        self, vector_store: VectorStore
    ) -> None:
        """A single delete_collection() call clears every chunk in the
        profile's collection, not just the first ingested source's — a
        profile with 2 sources sharing one collection should end up with
        the whole collection gone, not partially cleaned."""
        profile_id = uuid4()
        user_id = uuid4()
        source_id_a = str(uuid4())
        source_id_b = str(uuid4())
        collection_name = f"profile_{profile_id}"

        # Two ingested sources' chunks land in the same profile collection.
        chunk_a = FakeChunk(
            id=str(uuid4()), source_id=source_id_a, text="Experienced Python engineer"
        )
        chunk_b = FakeChunk(
            id=str(uuid4()), source_id=source_id_b, text="Contributed to open source"
        )
        vector_store.add_chunks(
            [(chunk_a, [0.1, 0.2, 0.3]), (chunk_b, [0.4, 0.5, 0.6])], collection_name
        )

        # Sanity check both embeddings exist before deletion.
        assert vector_store.get_collection(collection_name).count() == 2

        fake_profile = Mock(id=profile_id, user_id=user_id)
        fake_source_a = Mock(id=source_id_a, profile_id=profile_id)
        fake_source_b = Mock(id=source_id_b, profile_id=profile_id)
        mock_db = self._mock_db([fake_source_a, fake_source_b])

        async def fake_get_profile(db: Any, pid: UUID, uid: UUID) -> Mock:
            return fake_profile

        with (
            patch("core.services.profile_service.get_profile", fake_get_profile),
            patch("core.services.profile_service.VectorStore", return_value=vector_store),
        ):
            deleted = await delete_profile(mock_db, profile_id, user_id)

        assert deleted is True

        # A single delete_collection() call should clear both sources' chunks
        # at once, not just the first source's.
        remaining_collections = [c.name for c in vector_store.client.list_collections()]
        assert collection_name not in remaining_collections, (
            f"Expected delete_profile() to remove the '{collection_name}' ChromaDB "
            f"collection covering both ingested sources, but it still exists."
        )

    @pytest.mark.asyncio
    async def test_delete_profile_without_ingested_sources_does_not_raise(
        self, vector_store: VectorStore
    ) -> None:
        """A profile with zero ingested sources never had a ChromaDB
        collection created for it, so deleting it must not error out
        trying to clean up a collection that was never there."""
        profile_id = uuid4()
        user_id = uuid4()

        fake_profile = Mock(id=profile_id, user_id=user_id)
        mock_db = self._mock_db([])

        async def fake_get_profile(db: Any, pid: UUID, uid: UUID) -> Mock:
            return fake_profile

        with (
            patch("core.services.profile_service.get_profile", fake_get_profile),
            patch("core.services.profile_service.VectorStore", return_value=vector_store),
        ):
            deleted = await delete_profile(mock_db, profile_id, user_id)

        assert deleted is True
