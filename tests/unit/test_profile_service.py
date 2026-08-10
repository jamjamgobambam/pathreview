"""Unit tests for core.services.profile_service.delete_profile()'s
Postgres-side cascade behavior (issue #80).

Review and IngestedSource rows have DB-level ondelete="CASCADE" already,
but delete_profile() also deletes them explicitly before deleting the
Profile row itself. These tests assert that explicit cascade actually
happens against a mocked DB session.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from core.services.profile_service import delete_profile


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


@pytest.mark.unit
class TestDeleteProfileCascade:

    @pytest.mark.asyncio
    async def test_deletes_reviews_and_sources_and_commits(self) -> None:
        """Deleting a profile with reviews and sources deletes each row
        individually and commits once, instead of relying solely on the
        DB-level ondelete="CASCADE" to do the work."""
        profile_id = uuid4()
        user_id = uuid4()
        fake_profile = Mock(id=profile_id, user_id=user_id)
        fake_review = Mock(id=uuid4(), profile_id=profile_id)
        fake_source = Mock(id=uuid4(), profile_id=profile_id)

        mock_db = AsyncMock()
        review_result = Mock()
        review_result.scalars.return_value.all.return_value = [fake_review]
        source_result = Mock()
        source_result.scalars.return_value.all.return_value = [fake_source]
        mock_db.execute = AsyncMock(side_effect=[review_result, source_result])
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        async def fake_get_profile(db: Any, pid: UUID, uid: UUID) -> Mock:
            return fake_profile

        with (
            patch("core.services.profile_service.get_profile", fake_get_profile),
            patch("core.services.profile_service.VectorStore"),
        ):
            deleted = await delete_profile(mock_db, profile_id, user_id)

        assert deleted is True
        assert mock_db.delete.await_count == 3  # review, source, profile
        mock_db.delete.assert_any_await(fake_review)
        mock_db.delete.assert_any_await(fake_source)
        mock_db.delete.assert_any_await(fake_profile)
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_profile_not_found(self) -> None:
        """A profile that doesn't exist (or isn't owned by this user) short-
        circuits to False before touching the DB or the vector store."""
        mock_db = AsyncMock()

        async def fake_get_profile(db: Any, pid: UUID, uid: UUID) -> None:
            return None

        with (
            patch("core.services.profile_service.get_profile", fake_get_profile),
            patch("core.services.profile_service.VectorStore") as mock_vector_store,
        ):
            deleted = await delete_profile(mock_db, uuid4(), uuid4())

        assert deleted is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_vector_store.assert_not_called()

    @pytest.mark.asyncio
    async def test_rolls_back_when_vector_store_cleanup_fails(self) -> None:
        """If VectorStore.delete_collection() raises, delete_profile() must
        roll back and re-raise instead of committing the SQL deletes anyway
        — otherwise a Chroma failure would silently orphan embeddings again,
        the exact bug this fix is meant to close."""
        profile_id = uuid4()
        user_id = uuid4()
        fake_profile = Mock(id=profile_id, user_id=user_id)
        mock_db = _mock_db([])

        async def fake_get_profile(db: Any, pid: UUID, uid: UUID) -> Mock:
            return fake_profile

        mock_vector_store_instance = Mock()
        mock_vector_store_instance.delete_collection.side_effect = RuntimeError(
            "chroma unreachable"
        )

        with (
            patch("core.services.profile_service.get_profile", fake_get_profile),
            patch(
                "core.services.profile_service.VectorStore",
                return_value=mock_vector_store_instance,
            ),
            pytest.raises(RuntimeError),
        ):
            await delete_profile(mock_db, profile_id, user_id)

        mock_db.commit.assert_not_called()
        mock_db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_partial_failure_when_commit_fails_after_vector_cleanup(self) -> None:
        """Documents a known residual inconsistency: delete_collection() runs
        before db.commit(), so if commit() itself fails, the SQL side rolls
        back (profile row survives) but the ChromaDB collection is already
        gone and can't be un-deleted. The two systems aren't fully atomic —
        this pins down exactly which failure mode still exists."""
        profile_id = uuid4()
        user_id = uuid4()
        fake_profile = Mock(id=profile_id, user_id=user_id)
        mock_db = _mock_db([])
        mock_db.commit.side_effect = RuntimeError("db commit failed")

        async def fake_get_profile(db: Any, pid: UUID, uid: UUID) -> Mock:
            return fake_profile

        mock_vector_store_instance = Mock()

        with (
            patch("core.services.profile_service.get_profile", fake_get_profile),
            patch(
                "core.services.profile_service.VectorStore",
                return_value=mock_vector_store_instance,
            ),
            pytest.raises(RuntimeError),
        ):
            await delete_profile(mock_db, profile_id, user_id)

        # The vector store cleanup already ran and can't be undone, even
        # though the SQL side rolled back and the profile row still exists.
        mock_vector_store_instance.delete_collection.assert_called_once_with(
            f"profile_{profile_id}"
        )
        mock_db.rollback.assert_awaited_once()
