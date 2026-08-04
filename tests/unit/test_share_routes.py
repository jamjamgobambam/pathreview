"""Tests for share endpoints in api/routes/reviews.py"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from api.routes.reviews import create_share_token, get_public_review
from api.schemas.share import PublicReviewResponse, ShareTokenResponse


@pytest.mark.unit
class TestShareRoutes:
    """Test suite for share-related route handlers."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_user(self) -> Mock:
        """Create a mock authenticated User object.

        User.id is Mapped[str] (UUID stored as string), so we use str(uuid4()).
        """
        user = Mock()
        user.id = str(uuid4())
        return user

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create a mock FastAPI Request with a base_url."""
        request = Mock()
        request.base_url = "http://testserver/"
        return request

    @pytest.fixture
    def mock_complete_review(self) -> Mock:
        """Create a mock Review with status='complete'."""
        review = Mock()
        review.id = uuid4()
        review.status = "complete"
        review.overall_score = 0.85
        review.sections = None
        review.created_at = datetime.now(UTC)
        return review

    # ------------------------------------------------------------------
    # POST /{review_id}/share
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_share_token_success(
        self,
        mock_db_session: AsyncMock,
        mock_user: Mock,
        mock_request: Mock,
        mock_complete_review: Mock,
    ) -> None:
        """Happy path: returns ShareTokenResponse with token and share_url."""
        review_id = uuid4()

        # No existing active token in the DB
        no_token_result = Mock()
        no_token_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=no_token_result)

        # Simulate DB populating the token column default on refresh
        async def populate_token(obj: object) -> None:
            obj.token = "newtoken_abc123"  # type: ignore[attr-defined]

        mock_db_session.refresh = AsyncMock(side_effect=populate_token)

        with patch("api.routes.reviews.get_review", AsyncMock(return_value=mock_complete_review)):
            result = await create_share_token(
                review_id=review_id,
                request=mock_request,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(result, ShareTokenResponse)
        assert result.token == "newtoken_abc123"
        assert "newtoken_abc123" in result.share_url
        assert result.share_url.startswith("http://testserver")

    @pytest.mark.asyncio
    async def test_create_share_token_returns_existing_active(
        self,
        mock_db_session: AsyncMock,
        mock_user: Mock,
        mock_request: Mock,
        mock_complete_review: Mock,
    ) -> None:
        """Idempotent: returns existing unexpired token without creating a new one."""
        review_id = uuid4()

        existing_token = Mock()
        existing_token.token = "existing_token_xyz"
        existing_token.expires_at = datetime.now(UTC) + timedelta(days=15)

        existing_result = Mock()
        existing_result.scalars.return_value.first.return_value = existing_token
        mock_db_session.execute = AsyncMock(return_value=existing_result)

        with patch("api.routes.reviews.get_review", AsyncMock(return_value=mock_complete_review)):
            result = await create_share_token(
                review_id=review_id,
                request=mock_request,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(result, ShareTokenResponse)
        assert result.token == "existing_token_xyz"
        # db.add must NOT have been called — no new token was inserted
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_share_token_review_not_found(
        self, mock_db_session: AsyncMock, mock_user: Mock, mock_request: Mock
    ) -> None:
        """404 when review is not found or does not belong to current user."""
        review_id = uuid4()

        with (
            patch("api.routes.reviews.get_review", AsyncMock(return_value=None)),
            pytest.raises(HTTPException) as exc_info,
        ):
            await create_share_token(
                review_id=review_id,
                request=mock_request,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_share_token_review_not_complete(
        self, mock_db_session: AsyncMock, mock_user: Mock, mock_request: Mock
    ) -> None:
        """400 when review exists but has not completed processing."""
        review_id = uuid4()

        pending_review = Mock()
        pending_review.status = "pending"

        with (
            patch("api.routes.reviews.get_review", AsyncMock(return_value=pending_review)),
            pytest.raises(HTTPException) as exc_info,
        ):
            await create_share_token(
                review_id=review_id,
                request=mock_request,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 400

    # ------------------------------------------------------------------
    # GET /public/{token}
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_public_review_success(self, mock_db_session: AsyncMock) -> None:
        """Valid, unexpired token returns PublicReviewResponse with review data."""
        review_id = uuid4()

        mock_review = Mock()
        mock_review.id = review_id
        mock_review.overall_score = 0.85
        mock_review.sections = None
        mock_review.created_at = datetime.now(UTC)
        mock_review.status = "complete"

        mock_share_token = Mock()
        mock_share_token.token = "valid_token_abc"
        mock_share_token.expires_at = datetime.now(UTC) + timedelta(days=15)
        mock_share_token.review = mock_review

        token_result = Mock()
        token_result.scalars.return_value.first.return_value = mock_share_token
        mock_db_session.execute = AsyncMock(return_value=token_result)

        result = await get_public_review(token="valid_token_abc", db=mock_db_session)

        assert isinstance(result, PublicReviewResponse)
        assert result.overall_score == 0.85

    @pytest.mark.asyncio
    async def test_get_public_review_expired(self, mock_db_session: AsyncMock) -> None:
        """410 Gone when the share token has passed its expiry date."""
        mock_share_token = Mock()
        mock_share_token.token = "expired_token"
        mock_share_token.expires_at = datetime.now(UTC) - timedelta(days=1)
        # tzinfo is set so the naive-tz branch is not hit
        mock_share_token.expires_at = datetime.now(UTC) - timedelta(days=1)

        expired_result = Mock()
        expired_result.scalars.return_value.first.return_value = mock_share_token
        mock_db_session.execute = AsyncMock(return_value=expired_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_public_review(token="expired_token", db=mock_db_session)

        assert exc_info.value.status_code == 410

    @pytest.mark.asyncio
    async def test_get_public_review_not_found(self, mock_db_session: AsyncMock) -> None:
        """404 for a token that does not exist in the database."""
        not_found_result = Mock()
        not_found_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=not_found_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_public_review(token="nonexistent_token", db=mock_db_session)

        assert exc_info.value.status_code == 404
