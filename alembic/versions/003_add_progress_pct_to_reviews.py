"""Add progress_pct column to reviews table.

Revision ID: 003
Revises: 002
Create Date: 2026-08-04 00:00:00.000000
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
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("reviews", "progress_pct")
