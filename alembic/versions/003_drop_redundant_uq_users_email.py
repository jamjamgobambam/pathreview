"""Drop redundant uq_users_email unique constraint.

Migration 001 created both a unique index (``ix_users_email``, from the model's
``unique=True, index=True`` on ``User.email``) and a separate named unique
constraint (``uq_users_email``). The two are redundant -- the unique index
already enforces uniqueness -- and the SQLAlchemy model only declares the
index, so the extra constraint shows up as schema drift under ``alembic check``.

Dropping it aligns the live schema with the models.

Revision ID: 003
Revises: 002
Create Date: 2026-07-17 00:00:00.000000
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
