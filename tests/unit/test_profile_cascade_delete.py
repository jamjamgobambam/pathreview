"""Cascade-delete of embeddings when a profile is deleted (issue #80).

Issue #80: DELETE /profiles/{profile_id} doesn't cascade to delete associated
reviews and embeddings.

What I found tracing it (AI201 Module 3, Week 8):
- delete_profile() in core/services/profile_service.py already removes the
  Review and IngestedSource rows in Postgres (and the models have ondelete=CASCADE
  on top of that), so the "reviews" half is effectively handled.
- The real, live gap was the embeddings. Each profile's vectors live in their own
  ChromaDB collection named f"profile_{profile_id}" (see rag/retriever/hybrid.py
  and rag/retriever/vector_store.py). Nothing in the delete path removed that
  collection, so the vectors stuck around forever pointing at a profile that no
  longer existed.

The Week 9 fix adds VectorStore.delete_collection() and has delete_profile()
call it (best-effort, after the SQL commit) so the collection is removed.

These tests seed a per-profile collection the way the ingestion path would, delete
the profile through the real service — injecting the same VectorStore the fix uses
so the test and the code agree on which store to clean — and check the collection
is gone. The no-op test covers a profile that never had embeddings.
"""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from core.services.profile_service import delete_profile
from rag.retriever.vector_store import VectorStore, collection_name_for_profile


@pytest.mark.unit
class TestProfileCascadeDeleteEmbeddings:
    """Profile deletion removes the profile's ChromaDB collection (#80)."""

    def _mock_db_returning(self, profile: Mock) -> AsyncMock:
        """Fake async DB session.

        get_profile() reads scalars().first(); the review/source lookups read
        scalars().all(). One result object covers all three calls: first()
        returns the profile, all() returns an empty list.

        Args:
            profile: The mock Profile row get_profile() should return.

        Returns:
            An AsyncMock session wired for the delete_profile() call path.
        """
        scalars = Mock()
        scalars.first.return_value = profile
        scalars.all.return_value = []

        result = Mock()
        result.scalars.return_value = scalars

        db = AsyncMock()
        db.execute = AsyncMock(return_value=result)
        db.delete = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_delete_profile_removes_chromadb_collection(self, tmp_path: Path) -> None:
        """Deleting a profile removes its per-profile ChromaDB collection."""
        profile_id = uuid.uuid4()
        user_id = uuid.uuid4()

        profile = Mock()
        profile.id = profile_id
        profile.user_id = user_id

        # Inject the same store the fix will clean up, backed by a temp dir.
        store = VectorStore(persist_dir=str(tmp_path))

        # Seed the per-profile collection the way ingestion does. The name matches
        # collection_name_for_profile(), the single source of truth both the fix
        # and the retrieval path use.
        collection_name = collection_name_for_profile(profile_id)
        collection = store.client.create_collection(name=collection_name)
        collection.add(
            ids=["chunk-1"],
            embeddings=[[0.1, 0.2, 0.3]],
            documents=["some ingested chunk"],
            metadatas=[{"source_id": "resume_x"}],
        )
        assert collection_name in [c.name for c in store.client.list_collections()]

        db = self._mock_db_returning(profile)

        deleted = await delete_profile(
            db=db, profile_id=profile_id, user_id=user_id, vector_store=store
        )
        assert deleted is True

        # The embeddings collection is gone — no orphaned vectors left behind.
        remaining = [c.name for c in store.client.list_collections()]
        assert collection_name not in remaining, (
            f"Orphaned embeddings: ChromaDB collection '{collection_name}' still "
            f"exists after the profile was deleted."
        )

    @pytest.mark.asyncio
    async def test_delete_profile_with_no_embeddings_is_a_clean_noop(self, tmp_path: Path) -> None:
        """A profile that never had embeddings deletes cleanly, no error raised."""
        profile_id = uuid.uuid4()
        user_id = uuid.uuid4()

        profile = Mock()
        profile.id = profile_id
        profile.user_id = user_id

        # Store exists but the profile's collection was never created.
        store = VectorStore(persist_dir=str(tmp_path))
        collection_name = collection_name_for_profile(profile_id)
        assert collection_name not in [c.name for c in store.client.list_collections()]

        db = self._mock_db_returning(profile)

        deleted = await delete_profile(
            db=db, profile_id=profile_id, user_id=user_id, vector_store=store
        )

        # No collection to remove is a no-op success, not a failure.
        assert deleted is True
        assert collection_name not in [c.name for c in store.client.list_collections()]
