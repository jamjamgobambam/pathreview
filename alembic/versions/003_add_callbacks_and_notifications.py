"""Add callbacks and notifications tables for the review-completed webhook.

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
    # Create callbacks table
    op.create_table(
        "callbacks",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_callbacks_user_id_users"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["profiles.id"],
            name=op.f("fk_callbacks_profile_id_profiles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_callbacks")),
        sa.UniqueConstraint("profile_id", name=op.f("uq_callbacks_profile_id")),
    )
    op.create_index(op.f("ix_callbacks_user_id"), "callbacks", ["user_id"])
    op.create_index(op.f("ix_callbacks_profile_id"), "callbacks", ["profile_id"], unique=True)

    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("callback_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("review_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("delivery_status", sa.String(20), nullable=False, server_default="retry"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_ack_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["callback_id"],
            ["callbacks.id"],
            name=op.f("fk_notifications_callback_id_callbacks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["reviews.id"],
            name=op.f("fk_notifications_review_id_reviews"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(op.f("ix_notifications_callback_id"), "notifications", ["callback_id"])
    op.create_index(op.f("ix_notifications_review_id"), "notifications", ["review_id"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("callbacks")
