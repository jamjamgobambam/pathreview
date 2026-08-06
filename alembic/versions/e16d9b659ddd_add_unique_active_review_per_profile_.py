"""add unique active review per profile index

Revision ID: e16d9b659ddd
Revises: 002
Create Date: 2026-08-03 18:46:32.647115

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "e16d9b659ddd"
down_revision: str | Sequence[str] | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
