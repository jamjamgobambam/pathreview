"""Tests for core/models/share_token.py"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from core.models.share_token import ShareToken


@pytest.mark.unit
class TestShareTokenModel:
    """Test suite for the ShareToken SQLAlchemy model."""

    def _make_token(self, **kwargs: Any) -> ShareToken:
        """Return a ShareToken instance with sensible defaults."""
        defaults = {
            "review_id": str(uuid4()),
            "expires_at": datetime.now(tz=UTC) + timedelta(days=30),
        }
        defaults.update(kwargs)
        return ShareToken(**defaults)

    # ------------------------------------------------------------------
    # Column structure
    # SQLAlchemy applies `default=` at INSERT time, not instantiation.
    # We verify that defaults are registered and check column types/constraints.
    # ------------------------------------------------------------------

    def _col(self, column_name: str) -> Any:
        """Return the Column object for a named column."""
        return ShareToken.__table__.c[column_name]

    def test_id_column_has_default(self) -> None:
        """The id column has a default registered."""
        assert self._col("id").default is not None

    def test_id_column_is_primary_key(self) -> None:
        """The id column is the primary key."""
        assert self._col("id").primary_key is True

    def test_token_column_has_default(self) -> None:
        """The token column has a default registered."""
        assert self._col("token").default is not None

    def test_token_column_is_unique(self) -> None:
        """The token column has a unique constraint."""
        assert self._col("token").unique is True

    def test_token_column_max_length(self) -> None:
        """The token column is String(64)."""
        from sqlalchemy import String

        col_type = self._col("token").type
        assert isinstance(col_type, String)
        assert col_type.length == 64

    def test_review_id_column_is_not_nullable(self) -> None:
        """The review_id column is NOT NULL."""
        assert self._col("review_id").nullable is False

    def test_expires_at_column_is_not_nullable(self) -> None:
        """The expires_at column is NOT NULL."""
        assert self._col("expires_at").nullable is False

    def test_created_at_column_has_default(self) -> None:
        """The created_at column has a default registered."""
        assert self._col("created_at").default is not None

    def test_token_uniqueness_via_secrets(self) -> None:
        """secrets.token_urlsafe(32) produces unique values — the underlying mechanism."""
        import secrets

        t1 = secrets.token_urlsafe(32)
        t2 = secrets.token_urlsafe(32)
        assert t1 != t2
        assert len(t1) <= 64

    def test_id_uniqueness_via_uuid4(self) -> None:
        """uuid4() produces unique values — the underlying mechanism for id defaults."""
        from uuid import uuid4

        assert str(uuid4()) != str(uuid4())

    # ------------------------------------------------------------------
    # Field assignment
    # ------------------------------------------------------------------

    def test_explicit_token_value_is_preserved(self) -> None:
        """An explicitly supplied token is not overwritten."""
        custom_token = "my-custom-token-abc123"
        share_token = self._make_token(token=custom_token)
        assert share_token.token == custom_token

    def test_review_id_is_stored(self) -> None:
        """Provided review_id is accessible on the instance."""
        review_id = str(uuid4())
        share_token = self._make_token(review_id=review_id)
        assert share_token.review_id == review_id

    def test_expires_at_is_stored(self) -> None:
        """Provided expires_at is accessible on the instance."""
        expiry = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
        share_token = self._make_token(expires_at=expiry)
        assert share_token.expires_at == expiry

    # ------------------------------------------------------------------
    # Table metadata
    # ------------------------------------------------------------------

    def test_tablename(self) -> None:
        """ShareToken maps to the share_tokens table."""
        assert ShareToken.__tablename__ == "share_tokens"

    # ------------------------------------------------------------------
    # __repr__
    # ------------------------------------------------------------------

    def test_repr_contains_id(self) -> None:
        """__repr__ includes the token's id."""
        share_token = self._make_token()
        share_token.id = "test-id-123"
        assert "test-id-123" in repr(share_token)

    def test_repr_contains_review_id(self) -> None:
        """__repr__ includes the review_id."""
        review_id = str(uuid4())
        share_token = self._make_token(review_id=review_id)
        assert review_id in repr(share_token)

    def test_repr_contains_expires_at(self) -> None:
        """__repr__ includes the expires_at timestamp."""
        expiry = datetime(2026, 9, 1, tzinfo=UTC)
        share_token = self._make_token(expires_at=expiry)
        assert "2026-09-01" in repr(share_token)

    def test_repr_format(self) -> None:
        """__repr__ starts with '<ShareToken('."""
        share_token = self._make_token()
        assert repr(share_token).startswith("<ShareToken(")

    # ------------------------------------------------------------------
    # Expiry helpers (logic only — no DB required)
    # ------------------------------------------------------------------

    def test_token_not_expired_when_future_expiry(self) -> None:
        """A token with a future expires_at is not yet expired."""
        share_token = self._make_token(expires_at=datetime.now(tz=UTC) + timedelta(days=1))
        assert share_token.expires_at > datetime.now(tz=UTC)

    def test_token_expired_when_past_expiry(self) -> None:
        """A token with a past expires_at is considered expired."""
        share_token = self._make_token(expires_at=datetime.now(tz=UTC) - timedelta(seconds=1))
        assert share_token.expires_at < datetime.now(tz=UTC)
