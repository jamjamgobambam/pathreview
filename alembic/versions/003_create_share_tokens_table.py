"""Create share_tokens table for time-limited public review sharing.

Revision ID: 003
Revises: 002
Create Date: 2026-08-02 00:00:00.000000
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
    """Create share_tokens table."""
    op.create_table(
        "share_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("review_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["reviews.id"],
            name=op.f("fk_share_tokens_review_id_reviews"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_share_tokens")),
        sa.UniqueConstraint("token", name=op.f("uq_share_tokens_token")),
    )
    op.create_index(op.f("ix_share_tokens_token"), "share_tokens", ["token"], unique=True)
    op.create_index(op.f("ix_share_tokens_review_id"), "share_tokens", ["review_id"])


def downgrade() -> None:
    """Drop share_tokens table."""
    op.drop_index(op.f("ix_share_tokens_review_id"), table_name="share_tokens")
    op.drop_index(op.f("ix_share_tokens_token"), table_name="share_tokens")
    op.drop_table("share_tokens")
