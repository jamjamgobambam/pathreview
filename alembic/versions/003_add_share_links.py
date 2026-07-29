"""Add share_links table for public review sharing.

Revision ID: 003
Revises: 002
Create Date: 2026-07-28 00:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op  # type: ignore[attr-defined]

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "share_links",
        sa.Column("token", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "review_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_share_links_review_id", "share_links", ["review_id"])


def downgrade() -> None:
    op.drop_index("ix_share_links_review_id", table_name="share_links")
    op.drop_table("share_links")
