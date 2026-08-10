"""Add is_public and share_expires_at columns to reviews table.

Revision ID: 003
Revises: 002
Create Date: 2026-08-01 00:00:00.000000
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
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "reviews",
        sa.Column("share_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reviews", "share_expires_at")
    op.drop_column("reviews", "is_public")
