"""Add webhook registrations and delivery tracking.

Revision ID: 003
Revises: 002
Create Date: 2026-08-09 00:00:00.000000
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
        "webhooks",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("secret", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_webhooks_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_webhooks")),
    )
    op.create_index(op.f("ix_webhooks_user_id"), "webhooks", ["user_id"])
    op.create_index(op.f("ix_webhooks_is_active"), "webhooks", ["is_active"])

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("webhook_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("review_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["webhook_id"],
            ["webhooks.id"],
            name=op.f("fk_webhook_deliveries_webhook_id_webhooks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["reviews.id"],
            name=op.f("fk_webhook_deliveries_review_id_reviews"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_webhook_deliveries")),
    )
    op.create_index(op.f("ix_webhook_deliveries_webhook_id"), "webhook_deliveries", ["webhook_id"])
    op.create_index(op.f("ix_webhook_deliveries_review_id"), "webhook_deliveries", ["review_id"])
    op.create_index(op.f("ix_webhook_deliveries_status"), "webhook_deliveries", ["status"])


def downgrade() -> None:
    op.drop_table("webhook_deliveries")
    op.drop_table("webhooks")
