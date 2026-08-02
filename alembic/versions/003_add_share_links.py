"""Add share_links table for public, tokenized review sharing.

Revision ID: 003
Revises: 002
Create Date: 2026-07-29 00:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create share_links table."""
    op.create_table(
        "share_links",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("review_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["reviews.id"],
            name=op.f("fk_share_links_review_id_reviews"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_share_links")),
        sa.UniqueConstraint("token", name=op.f("uq_share_links_token")),
    )
    op.create_index(op.f("ix_share_links_review_id"), "share_links", ["review_id"])
    op.create_index(op.f("ix_share_links_token"), "share_links", ["token"], unique=True)
    op.create_index(op.f("ix_share_links_expires_at"), "share_links", ["expires_at"])


def downgrade() -> None:
    """Drop share_links table."""
    op.drop_index(op.f("ix_share_links_expires_at"), table_name="share_links")
    op.drop_index(op.f("ix_share_links_token"), table_name="share_links")
    op.drop_index(op.f("ix_share_links_review_id"), table_name="share_links")
    op.drop_table("share_links")
