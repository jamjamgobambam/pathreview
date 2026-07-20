"""Reproduction test for issue #80: orphaned vector-store embeddings on profile delete.

Demonstrates that delete_profile correctly cascades SQL row deletions (Reviews,
IngestedSources, Profile) but never cleans up the ChromaDB collection
'profile_{profile_id}', leaving embeddings orphaned in the vector store.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from core.services.profile_service import delete_profile


@pytest.mark.unit
class TestDeleteProfileCascade:

    @pytest.fixture
    def profile_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def user_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def mock_profile(self, profile_id: UUID, user_id: UUID) -> Mock:
        profile = Mock()
        profile.id = profile_id
        profile.user_id = user_id
        return profile

    @pytest.fixture
    def mock_db(self, mock_profile: Mock) -> AsyncMock:
        """Mock async DB session wired for a successful profile deletion."""
        db = AsyncMock()

        # get_profile: db.execute → result.scalars().first() → mock_profile
        get_result = Mock()
        get_result.scalars.return_value.first.return_value = mock_profile

        # Review query: db.execute → result.scalars().all() → []
        reviews_result = Mock()
        reviews_result.scalars.return_value.all.return_value = []

        # IngestedSource query: db.execute → result.scalars().all() → []
        sources_result = Mock()
        sources_result.scalars.return_value.all.return_value = []

        db.execute = AsyncMock(side_effect=[get_result, reviews_result, sources_result])
        db.delete = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_delete_profile_returns_false_when_not_found(
        self, mock_db: AsyncMock, profile_id: UUID, user_id: UUID
    ) -> None:
        """delete_profile returns False when the profile doesn't exist or isn't owned by user."""
        not_found_result = Mock()
        not_found_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=not_found_result)

        result = await delete_profile(db=mock_db, profile_id=profile_id, user_id=user_id)

        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_profile_cascades_sql_rows(
        self, mock_db: AsyncMock, profile_id: UUID, user_id: UUID, mock_profile: Mock
    ) -> None:
        """delete_profile commits the DB transaction that removes the profile and related rows."""
        await delete_profile(db=mock_db, profile_id=profile_id, user_id=user_id)

        mock_db.commit.assert_called_once()
        mock_db.delete.assert_called_with(mock_profile)

    @pytest.mark.asyncio
    async def test_delete_profile_cleans_up_vector_store_collection(
        self, mock_db: AsyncMock, profile_id: UUID, user_id: UUID
    ) -> None:
        """FAILING — issue #80: delete_profile must remove the profile's ChromaDB collection.

        Expected: VectorStore().delete_collection(f"profile_{profile_id}") is called
                  so no orphaned embeddings remain after the profile is deleted.
        Actual:   VectorStore is never touched; the collection persists in ChromaDB.

        After the fix, update the patch path from 'rag.retriever.vector_store.VectorStore'
        to 'core.services.profile_service.VectorStore' (where it will be imported).
        """
        with patch("rag.retriever.vector_store.VectorStore") as mock_vs_cls:
            mock_vs = Mock()
            mock_vs_cls.return_value = mock_vs

            result = await delete_profile(db=mock_db, profile_id=profile_id, user_id=user_id)

            assert result is True
            # BUG: fails — VectorStore is never instantiated or called in delete_profile
            mock_vs.delete_collection.assert_called_once_with(f"profile_{profile_id}")
