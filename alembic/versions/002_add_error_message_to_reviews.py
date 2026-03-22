"""Add error_message column to reviews table.

Revision ID: 002
Revises: 001
Create Date: 2026-03-22 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reviews",
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reviews", "error_message")
