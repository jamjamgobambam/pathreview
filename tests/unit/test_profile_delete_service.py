"""Tests for profile_deletion_cascade issue #80"""


import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch

from core.services.profile_service import delete_profile


@pytest.mark.unit
class TestDeleteProfile:
    """Tests for profile deletion cascade to ChromaDB (issue #80)."""

    @pytest.fixture
    def fake_db(self):
        """Create fake async database session."""
        db = AsyncMock()
        db.delete = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_delete_profile_removes_embeddings(self, fake_db):
        """delete_profile deletes the profile's ChromaDB collection."""
        profile_id = uuid4()
        user_id = uuid4()
        fake_profile = Mock()
        fake_result = Mock()
        fake_result.scalars.return_value.all.return_value = []
        fake_db.execute.return_value = fake_result

        with patch(
            "core.services.profile_service.get_profile",
            new=AsyncMock(return_value=fake_profile),
        ):
            with patch("core.services.profile_service.VectorStore") as FakeVectorStore:
                result = await delete_profile(fake_db, profile_id, user_id)

                vector_store = FakeVectorStore.return_value
                vector_store.delete_collection.assert_called_once_with(
                    f"profile_{profile_id}"
                )
        assert result is True

    @pytest.mark.asyncio
    async def test_deleting_missing_profile_returns_false(self, fake_db):
        """delete_profile returns False and skips ChromaDB when the profile is missing."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch(
            "core.services.profile_service.get_profile",
            new=AsyncMock(return_value=None),
        ):
            with patch("core.services.profile_service.VectorStore") as FakeVectorStore:
                result = await delete_profile(fake_db, profile_id, user_id)

        assert result is False
        FakeVectorStore.assert_not_called()
