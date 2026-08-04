"""Unit tests for the User model's schema declarations."""

import pytest
from sqlalchemy import UniqueConstraint

from core.models.user import User


@pytest.mark.unit
class TestUserModelSchema:
    """Schema-level checks that the User model matches its migration."""

    def test_email_unique_constraint_declared(self) -> None:
        """User declares the named ``uq_users_email`` unique constraint.

        Migration ``001`` creates a named unique constraint on ``users.email``.
        The model must declare the same constraint on ``Base.metadata`` so that
        ``alembic check`` finds no drift between the migrations and the models
        (see scripts/validate_migrations.sh). Without it, the migration ships a
        constraint the models don't know about.
        """
        unique_constraint_names = {
            constraint.name
            for constraint in User.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }

        assert "uq_users_email" in unique_constraint_names
