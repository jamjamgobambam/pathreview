"""Tests for the public share-link feature (issue #101).

Covers the service functions (create_share_link, get_share_link) and the
route logic for the public view endpoint (404 for unknown/malformed tokens,
410 for expired links, success for valid links) and the authed mint endpoint
(ownership check).
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from api.routes.reviews import create_share_link_endpoint, get_shared_review_endpoint
from core.services.review_service import create_share_link, get_share_link


@pytest.mark.unit
class TestShareLinkService:
    """Unit tests for the share-link service functions."""

    @pytest.mark.asyncio
    async def test_create_share_link_persists_and_sets_30_day_expiry(self):
        db = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        review_id = uuid4()

        with patch("core.services.review_service.ShareLink") as mock_share_link_cls:
            instance = mock_share_link_cls.return_value
            result = await create_share_link(db, review_id)

            kwargs = mock_share_link_cls.call_args[1]
            assert kwargs["review_id"] == review_id
            delta = kwargs["expires_at"] - datetime.utcnow()
            # ~30 days out (allow a small window for execution time).
            assert timedelta(days=29, hours=23) < delta <= timedelta(days=30)

            db.add.assert_called_once_with(instance)
            db.commit.assert_awaited_once()
            db.refresh.assert_awaited_once_with(instance)
            assert result is instance

    @pytest.mark.asyncio
    async def test_get_share_link_returns_row_when_found(self):
        db = AsyncMock()
        link = Mock()
        result_mock = Mock()
        result_mock.scalars.return_value.first.return_value = link
        db.execute = AsyncMock(return_value=result_mock)

        out = await get_share_link(db, str(uuid4()))

        assert out is link
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_share_link_returns_none_when_missing(self):
        db = AsyncMock()
        result_mock = Mock()
        result_mock.scalars.return_value.first.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        out = await get_share_link(db, str(uuid4()))

        assert out is None


@pytest.mark.unit
class TestPublicShareRoute:
    """Unit tests for GET /reviews/shared/{token} logic (called directly)."""

    @pytest.mark.asyncio
    async def test_malformed_token_returns_404(self):
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await get_shared_review_endpoint(token="not-a-uuid", db=db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_unknown_token_returns_404(self):
        db = AsyncMock()
        with (
            patch("api.routes.reviews.get_share_link", new=AsyncMock(return_value=None)),
            pytest.raises(HTTPException) as exc_info,
        ):
            await get_shared_review_endpoint(token=str(uuid4()), db=db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_expired_token_returns_410(self):
        db = AsyncMock()
        expired_link = Mock()
        expired_link.expires_at = datetime.now(UTC) - timedelta(days=1)
        expired_link.review = Mock()

        with (
            patch(
                "api.routes.reviews.get_share_link",
                new=AsyncMock(return_value=expired_link),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await get_shared_review_endpoint(token=str(uuid4()), db=db)
        assert exc_info.value.status_code == 410

    @pytest.mark.asyncio
    async def test_valid_token_returns_public_view(self):
        db = AsyncMock()
        link = Mock()
        link.expires_at = datetime.now(UTC) + timedelta(days=10)
        review = Mock()
        review.overall_score = 0.8
        review.sections = [
            {
                "section_name": "Technical Skills",
                "content": "Solid",
                "confidence": 0.9,
                "suggestions": ["Add tests"],
            }
        ]
        review.created_at = datetime.now(UTC)
        link.review = review

        with patch("api.routes.reviews.get_share_link", new=AsyncMock(return_value=link)):
            result = await get_shared_review_endpoint(token=str(uuid4()), db=db)

        assert result.overall_score == 0.8
        assert result.sections is not None
        assert result.sections[0].section_name == "Technical Skills"


@pytest.mark.unit
class TestMintShareRoute:
    """Unit tests for POST /reviews/{review_id}/share ownership handling."""

    @pytest.mark.asyncio
    async def test_owner_gets_share_link(self):
        db = AsyncMock()
        user = Mock()
        user.id = str(uuid4())
        link = Mock()
        link.token = str(uuid4())
        link.expires_at = datetime.now(UTC) + timedelta(days=30)

        with (
            patch("api.routes.reviews.get_review", new=AsyncMock(return_value=Mock())),
            patch("api.routes.reviews.create_share_link", new=AsyncMock(return_value=link)),
        ):
            result = await create_share_link_endpoint(review_id=uuid4(), current_user=user, db=db)

        assert result.token == link.token

    @pytest.mark.asyncio
    async def test_non_owner_or_missing_review_returns_404(self):
        db = AsyncMock()
        user = Mock()
        user.id = str(uuid4())

        with (
            patch("api.routes.reviews.get_review", new=AsyncMock(return_value=None)),
            pytest.raises(HTTPException) as exc_info,
        ):
            await create_share_link_endpoint(review_id=uuid4(), current_user=user, db=db)
        assert exc_info.value.status_code == 404
