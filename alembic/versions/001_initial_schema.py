"""Initial schema creation for users, profiles, ingested_sources, and reviews.

Revision ID: 001
Create Date: 2026-03-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index("ix_users_email_active", "users", ["email", "is_active"])

    # Create profiles table
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("github_username", sa.String(255), nullable=True),
        sa.Column("resume_filename", sa.String(255), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("portfolio_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_profiles_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_profiles")),
    )
    op.create_index(op.f("ix_profiles_user_id"), "profiles", ["user_id"])
    op.create_index(op.f("ix_profiles_github_username"), "profiles", ["github_username"])

    # Create ingested_sources table
    op.create_table(
        "ingested_sources",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("filename", sa.String(255), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], name=op.f("fk_ingested_sources_profile_id_profiles"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingested_sources")),
    )
    op.create_index(op.f("ix_ingested_sources_profile_id"), "ingested_sources", ["profile_id"])
    op.create_index(op.f("ix_ingested_sources_content_hash"), "ingested_sources", ["content_hash"])
    op.create_index(op.f("ix_ingested_sources_source_type"), "ingested_sources", ["source_type"])

    # Create reviews table
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("sections", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], name=op.f("fk_reviews_profile_id_profiles"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
    )
    op.create_index(op.f("ix_reviews_profile_id"), "reviews", ["profile_id"])
    op.create_index(op.f("ix_reviews_status"), "reviews", ["status"])
    op.create_index(op.f("ix_reviews_created_at"), "reviews", ["created_at"])


def downgrade() -> None:
    """Drop initial database schema."""
    # Drop tables in reverse order of creation (respecting foreign keys)
    op.drop_table("reviews")
    op.drop_table("ingested_sources")
    op.drop_table("profiles")
    op.drop_table("users")
