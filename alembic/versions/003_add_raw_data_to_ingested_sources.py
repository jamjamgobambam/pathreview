"""Add raw_data column to ingested_sources table.

Revision ID: 003
Revises: 002
Create Date: 2026-08-03 00:00:00.000000
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
        sa.Column("raw_data", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ingested_sources", "raw_data")
