"""Regression tests for issue #80: profile deletion must clean up vector store embeddings."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from core.services.profile_service import delete_profile
from rag.retriever.vector_store import VectorStore


@pytest.mark.unit
class TestProfileDeletionVectorCleanup:
    """Verifies delete_profile() removes the profile's Chroma collection."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        session = AsyncMock()
        session.add = Mock()
        session.delete = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def profile_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def seeded_vector_store(self, tmp_path: Path, profile_id: UUID) -> VectorStore:
        """A real VectorStore with one chunk embedded for the profile's collection."""
        store = VectorStore(persist_dir=str(tmp_path))
        chunk = Mock(
            id="chunk-1",
            source_id="resume_1",
            chunk_index=0,
            section="experience",
            text="Built REST APIs.",
        )
        store.add_chunks([(chunk, [0.1, 0.2, 0.3])], collection_name=f"profile_{profile_id}")
        return store

    @pytest.fixture
    def empty_vector_store(self, tmp_path: Path) -> VectorStore:
        """A real VectorStore with no collections created yet."""
        return VectorStore(persist_dir=str(tmp_path))

    def _mock_execute_sequence(self, mock_db_session: AsyncMock, profile: Mock) -> None:
        """delete_profile() calls db.execute() three times: get_profile, reviews, ingested_sources.

        The objects returned by `await db.execute(...)` are synchronous result
        objects (SQLAlchemy's `Result`), so they must be plain `Mock`s, not
        `AsyncMock`s — otherwise `.scalars()` itself becomes an unawaited coroutine.
        """
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = profile

        reviews_result = Mock()
        reviews_result.scalars.return_value.all.return_value = []

        sources_result = Mock()
        sources_result.scalars.return_value.all.return_value = []

        mock_db_session.execute = AsyncMock(
            side_effect=[profile_result, reviews_result, sources_result]
        )

    @pytest.mark.asyncio
    async def test_delete_profile_removes_vector_store_collection(
        self, mock_db_session: AsyncMock, seeded_vector_store: VectorStore, profile_id: UUID
    ) -> None:
        """Fixes #80: after delete_profile() succeeds, the profile's Chroma
        collection and its embeddings are gone, not just the Postgres rows."""
        user_id = uuid4()
        profile = Mock()
        profile.id = profile_id
        self._mock_execute_sequence(mock_db_session, profile)

        deleted = await delete_profile(mock_db_session, profile_id, user_id, seeded_vector_store)
        assert deleted is True

        collection = seeded_vector_store.get_collection(f"profile_{profile_id}")
        remaining = collection.get(include=["documents"])
        assert remaining["ids"] == []

    @pytest.mark.asyncio
    async def test_delete_profile_with_no_vector_collection_does_not_raise(
        self, mock_db_session: AsyncMock, empty_vector_store: VectorStore, profile_id: UUID
    ) -> None:
        """Edge case: a profile that was never ingested has no Chroma collection at all."""
        user_id = uuid4()
        profile = Mock()
        profile.id = profile_id
        self._mock_execute_sequence(mock_db_session, profile)

        deleted = await delete_profile(mock_db_session, profile_id, user_id, empty_vector_store)
        assert deleted is True
