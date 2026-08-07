"""Add review_shares table for public share tokens.

Revision ID: 003
Revises: 002
Create Date: 2026-07-30 00:00:00.000000
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
        "review_shares",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "review_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("share_token", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_shares_share_token", "review_shares", ["share_token"])
    op.create_index("ix_review_shares_review_id", "review_shares", ["review_id"])


def downgrade() -> None:
    op.drop_index("ix_review_shares_review_id", table_name="review_shares")
    op.drop_index("ix_review_shares_share_token", table_name="review_shares")
    op.drop_table("review_shares")
