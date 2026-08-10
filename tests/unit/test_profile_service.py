"""Tests for profile_service.py, focused on delete_profile's cascade behavior
(issue #80: DELETE /profiles/{profile_id} left orphaned vector embeddings).
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest

from core.services.profile_service import delete_profile
from rag.retriever.vector_store import VectorStore


def _execute_result(items):
    """Build the mock chain for `(await db.execute(stmt)).scalars().all()` /
    `.first()`.

    NOTE: db.execute() is async, but the SQLAlchemy Result it returns is used
    synchronously (`.scalars().all()`, `.scalars().first()`). The object
    returned by execute() must therefore be a plain MagicMock, not an
    AsyncMock — an AsyncMock's un-configured child attributes are themselves
    AsyncMock by default, so calling `.scalars()` on one returns an unawaited
    coroutine instead of a ScalarResult. (This is the exact bug behind the
    pre-existing failures in tests/unit/test_review_service.py.)
    """
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    result.scalars.return_value.first.return_value = items[0] if items else None
    return result


@pytest.mark.unit
class TestDeleteProfile:
    """Test suite for delete_profile."""

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock()
        session.delete = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_profile(self):
        profile = Mock()
        profile.id = uuid4()
        return profile

    @pytest.mark.asyncio
    async def test_returns_false_when_profile_not_found(self, mock_db_session):
        profile_id = uuid4()
        user_id = uuid4()

        mock_db_session.execute = AsyncMock(return_value=_execute_result([]))

        result = await delete_profile(mock_db_session, profile_id, user_id)

        assert result is False
        mock_db_session.commit.assert_not_called()
        mock_db_session.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_deletes_vector_store_collection_named_for_the_profile(
        self, mock_db_session, mock_profile
    ):
        """Core regression coverage for issue #80: the profile's own ChromaDB
        collection — profile_{profile_id} — must be deleted."""
        user_id = uuid4()
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _execute_result([mock_profile]),  # get_profile
                _execute_result([]),  # reviews
                _execute_result([]),  # ingested_sources
            ]
        )
        mock_vector_store = Mock(spec=VectorStore)

        result = await delete_profile(
            mock_db_session, mock_profile.id, user_id, vector_store=mock_vector_store
        )

        assert result is True
        mock_vector_store.delete_collection.assert_called_once_with(f"profile_{mock_profile.id}")
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deletes_reviews_and_ingested_sources_and_the_profile(
        self, mock_db_session, mock_profile
    ):
        user_id = uuid4()
        review1, review2 = Mock(), Mock()
        source1 = Mock()
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _execute_result([mock_profile]),
                _execute_result([review1, review2]),
                _execute_result([source1]),
            ]
        )

        await delete_profile(
            mock_db_session, mock_profile.id, user_id, vector_store=Mock(spec=VectorStore)
        )

        deleted = [call.args[0] for call in mock_db_session.delete.call_args_list]
        assert deleted == [review1, review2, source1, mock_profile]

    @pytest.mark.asyncio
    async def test_vector_store_failure_leaves_postgres_untouched(
        self, mock_db_session, mock_profile
    ):
        """If the vector store delete fails, nothing in Postgres should be
        deleted or committed — the whole operation should be safely
        retryable instead of leaving the two stores disagreeing."""
        user_id = uuid4()
        mock_db_session.execute = AsyncMock(return_value=_execute_result([mock_profile]))
        mock_vector_store = Mock(spec=VectorStore)
        mock_vector_store.delete_collection.side_effect = RuntimeError("chroma unreachable")

        with pytest.raises(RuntimeError):
            await delete_profile(
                mock_db_session, mock_profile.id, user_id, vector_store=mock_vector_store
            )

        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_constructs_a_default_vector_store_when_none_injected(
        self, mock_db_session, mock_profile
    ):
        """The route layer doesn't inject a vector_store, so delete_profile
        must build its own VectorStore() when one isn't provided."""
        user_id = uuid4()
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _execute_result([mock_profile]),
                _execute_result([]),
                _execute_result([]),
            ]
        )

        with patch("core.services.profile_service.VectorStore") as MockVectorStore:
            result = await delete_profile(mock_db_session, mock_profile.id, user_id)

        assert result is True
        MockVectorStore.assert_called_once_with()
        MockVectorStore.return_value.delete_collection.assert_called_once_with(
            f"profile_{mock_profile.id}"
        )
