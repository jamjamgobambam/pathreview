"""Tests for core/models/user.py"""

import pytest

from core.models import User


@pytest.mark.unit
class TestUserModel:
    """Test suite for the User model's table metadata."""

    def test_email_has_named_unique_constraint(self):
        """Test users.email has an explicit uq_users_email UniqueConstraint.

        Regression test: migration 001 creates this constraint, but the
        model previously only declared `unique=True` on the column, which
        produces a unique index rather than a named UniqueConstraint. That
        mismatch made `alembic check` report schema drift on a freshly
        migrated database. See issue #129.
        """
        constraint_names = {
            constraint.name
            for constraint in User.__table__.constraints
            if constraint.__class__.__name__ == "UniqueConstraint"
        }

        assert "uq_users_email" in constraint_names

    def test_email_column_is_unique_and_indexed(self):
        """Test the email column still enforces uniqueness via its index."""
        email_column = User.__table__.columns["email"]

        assert email_column.unique is True
        assert email_column.index is True

    def test_email_active_composite_index_present(self):
        """Test the ix_users_email_active composite index is unaffected."""
        index_names = {index.name for index in User.__table__.indexes}

        assert "ix_users_email_active" in index_names
