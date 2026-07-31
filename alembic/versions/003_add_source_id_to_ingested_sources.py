"""Add source_id column to ingested_sources table.

Revision ID: 003
Revises: 002
Create Date: 2026-07-21 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ingested_sources",
        sa.Column("source_id", sa.String(255), nullable=True),
    )
    op.create_index(
        op.f("ix_ingested_sources_source_id"),
        "ingested_sources",
        ["source_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ingested_sources_source_id"), table_name="ingested_sources")
    op.drop_column("ingested_sources", "source_id")
