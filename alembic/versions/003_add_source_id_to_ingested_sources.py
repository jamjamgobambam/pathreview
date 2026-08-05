"""Add source_id dedup key to ingested_sources table.

Gives IngestionPipeline a real deduplication key to check and record against.
Nullable because rows created by ingestion paths other than IngestionPipeline
(e.g. core/services/review_service.py) carry no dedup key; Postgres permits
multiple NULLs under a UNIQUE constraint, so those rows never collide.

Safe to apply as UNIQUE on an existing deployment: _record_ingested_source()
only ever logged, so no ingested_sources row has ever been persisted by the
pipeline (verified locally: `select count(*) from ingested_sources` -> 0).

Revision ID: 003
Revises: 002
Create Date: 2026-07-28 00:00:00.000000
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
        "ix_ingested_sources_source_id",
        "ingested_sources",
        ["source_id"],
    )
    op.create_unique_constraint(
        "uq_ingested_sources_source_id",
        "ingested_sources",
        ["source_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_ingested_sources_source_id",
        "ingested_sources",
        type_="unique",
    )
    op.drop_index("ix_ingested_sources_source_id", table_name="ingested_sources")
    op.drop_column("ingested_sources", "source_id")
