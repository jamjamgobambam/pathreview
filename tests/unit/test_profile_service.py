"""Tests for profile_service.py, focused on cascade delete behavior (issue #80)."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from core.services.profile_service import delete_profile


def _execute_result(*, first: Mock | None = None, all_: list[Mock] | None = None) -> Mock:
    """Build a mock SQLAlchemy execute() result for scalars().first()/.all()."""
    result = Mock()
    result.scalars.return_value.first.return_value = first
    result.scalars.return_value.all.return_value = all_ or []
    return result


@pytest.mark.unit
class TestDeleteProfileCascade:
    """Test suite for delete_profile's cascade behavior."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.delete = AsyncMock()
        return session

    @pytest.fixture
    def mock_vector_store(self) -> Mock:
        """Mock VectorStore so tests stay isolated (no real ChromaDB on disk)."""
        store = Mock()
        store.delete_collection = Mock()
        return store

    @pytest.fixture
    def mock_profile(self) -> Mock:
        """Create a mock Profile owned by the deleting user."""
        profile = Mock()
        profile.id = uuid4()
        profile.user_id = uuid4()
        return profile

    @pytest.fixture
    def mock_reviews(self) -> list[Mock]:
        """Create mock Review rows belonging to the profile."""
        return [Mock(id=uuid4()) for _ in range(3)]

    @pytest.fixture
    def mock_sources(self) -> list[Mock]:
        """Create mock IngestedSource rows belonging to the profile."""
        return [Mock(id=uuid4()) for _ in range(2)]

    @pytest.mark.asyncio
    async def test_delete_profile_returns_false_when_not_found(
        self, mock_db_session: AsyncMock
    ) -> None:
        """delete_profile returns False and touches nothing when the profile doesn't exist."""
        mock_db_session.execute.return_value = _execute_result(first=None)

        result = await delete_profile(db=mock_db_session, profile_id=uuid4(), user_id=uuid4())

        assert result is False
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_profile_removes_all_reviews_and_sources_no_orphans(
        self,
        mock_db_session: AsyncMock,
        mock_profile: Mock,
        mock_reviews: list[Mock],
        mock_sources: list[Mock],
        mock_vector_store: Mock,
    ) -> None:
        """delete_profile deletes every review and ingested source, leaving no orphans."""
        mock_db_session.execute.side_effect = [
            _execute_result(first=mock_profile),  # get_profile lookup
            _execute_result(all_=mock_reviews),  # reviews for profile_id
            _execute_result(all_=mock_sources),  # ingested sources for profile_id
        ]

        result = await delete_profile(
            db=mock_db_session,
            profile_id=mock_profile.id,
            user_id=mock_profile.user_id,
            vector_store=mock_vector_store,
        )

        assert result is True

        deleted_objects = [call.args[0] for call in mock_db_session.delete.call_args_list]

        # Every review and every ingested source must have been deleted.
        for review in mock_reviews:
            assert review in deleted_objects
        for source in mock_sources:
            assert source in deleted_objects

        # The profile row itself must also be deleted.
        assert mock_profile in deleted_objects

        # Total deletes == reviews + sources + the profile (no leftovers, nothing extra).
        assert len(deleted_objects) == len(mock_reviews) + len(mock_sources) + 1

        # The profile's embeddings collection must also be cleaned up (#80).
        mock_vector_store.delete_collection.assert_called_once_with(f"profile_{mock_profile.id}")

    @pytest.mark.asyncio
    async def test_delete_profile_commits_once_after_cascade(
        self,
        mock_db_session: AsyncMock,
        mock_profile: Mock,
        mock_reviews: list[Mock],
        mock_sources: list[Mock],
        mock_vector_store: Mock,
    ) -> None:
        """The cascade delete is committed as a single transaction."""
        mock_db_session.execute.side_effect = [
            _execute_result(first=mock_profile),
            _execute_result(all_=mock_reviews),
            _execute_result(all_=mock_sources),
        ]

        await delete_profile(
            db=mock_db_session,
            profile_id=mock_profile.id,
            user_id=mock_profile.user_id,
            vector_store=mock_vector_store,
        )

        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_profile_with_no_reviews_or_sources_still_deletes_profile(
        self, mock_db_session: AsyncMock, mock_profile: Mock, mock_vector_store: Mock
    ) -> None:
        """A profile with no child rows is still deleted cleanly."""
        mock_db_session.execute.side_effect = [
            _execute_result(first=mock_profile),
            _execute_result(all_=[]),
            _execute_result(all_=[]),
        ]

        result = await delete_profile(
            db=mock_db_session,
            profile_id=mock_profile.id,
            user_id=mock_profile.user_id,
            vector_store=mock_vector_store,
        )

        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_profile)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_profile_rolls_back_and_reraises_on_failure(
        self,
        mock_db_session: AsyncMock,
        mock_profile: Mock,
        mock_reviews: list[Mock],
        mock_sources: list[Mock],
    ) -> None:
        """If the cascade delete fails partway, the whole transaction is rolled back."""
        mock_db_session.execute.side_effect = [
            _execute_result(first=mock_profile),
            _execute_result(all_=mock_reviews),
            _execute_result(all_=mock_sources),
        ]
        mock_db_session.commit.side_effect = RuntimeError("db connection lost")

        with pytest.raises(RuntimeError):
            await delete_profile(
                db=mock_db_session, profile_id=mock_profile.id, user_id=mock_profile.user_id
            )

        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_profile_survives_embeddings_cleanup_failure(
        self, mock_db_session: AsyncMock, mock_profile: Mock, mock_vector_store: Mock
    ) -> None:
        """A ChromaDB failure after the SQL commit must not fail the delete (#80).

        Postgres and ChromaDB don't share a transaction. Once the SQL rows are
        committed the delete has effectively succeeded, so a failure while
        removing embeddings is logged best-effort rather than raised — otherwise
        a 500 would misreport a delete that already cleared the rows.
        """
        mock_db_session.execute.side_effect = [
            _execute_result(first=mock_profile),
            _execute_result(all_=[]),
            _execute_result(all_=[]),
        ]
        mock_vector_store.delete_collection.side_effect = RuntimeError("chroma unreachable")

        result = await delete_profile(
            db=mock_db_session,
            profile_id=mock_profile.id,
            user_id=mock_profile.user_id,
            vector_store=mock_vector_store,
        )

        assert result is True
        mock_db_session.commit.assert_called_once()
        mock_db_session.rollback.assert_not_called()
