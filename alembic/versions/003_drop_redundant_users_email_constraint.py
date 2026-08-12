"""Drop the redundant unique constraint on users.email.

Revision ID: 003
Revises: 002
Create Date: 2026-08-04 00:00:00.000000

The SQLAlchemy model defines users.email with both ``unique=True`` and
``index=True``. Alembic represents that definition as a unique index. The
initial migration also created a separate unique constraint, which causes
``alembic check`` to report schema drift. This corrective migration removes
only the redundant constraint; the unique index continues to enforce email
uniqueness.
"""

from alembic import op  # type: ignore[attr-defined]

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_users_email", "users", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("uq_users_email", "users", ["email"])
