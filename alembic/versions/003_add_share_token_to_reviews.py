"""Add share_token column to reviews table.

Revision ID: 003
Revises: 002
Create Date: 2026-08-02 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reviews",
        sa.Column("share_token", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_reviews_share_token",
        "reviews",
        ["share_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_reviews_share_token", table_name="reviews")
    op.drop_column("reviews", "share_token")
