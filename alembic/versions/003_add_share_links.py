"""Add share_links table for public, expiring review shares.

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
    """Create the share_links table."""
    op.create_table(
        "share_links",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("review_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["reviews.id"],
            name=op.f("fk_share_links_review_id_reviews"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_share_links")),
    )
    op.create_index(op.f("ix_share_links_token"), "share_links", ["token"], unique=True)
    op.create_index(op.f("ix_share_links_review_id"), "share_links", ["review_id"])


def downgrade() -> None:
    """Drop the share_links table."""
    op.drop_table("share_links")
