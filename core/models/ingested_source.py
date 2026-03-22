"""Ingested source model for tracking imported content."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class IngestedSource(Base):
    """Model for tracking ingested portfolio sources (resumes, READMEs, repos, web pages)."""

    __tablename__ = "ingested_sources"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    profile_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "resume", "readme", "repo", "web"
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)  # SHA256 hash for deduplication
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="ingested_sources")

    __table_args__ = (
        Index("ix_ingested_sources_profile_id", "profile_id"),
        Index("ix_ingested_sources_content_hash", "content_hash"),
        Index("ix_ingested_sources_source_type", "source_type"),
    )

    def __repr__(self) -> str:
        return f"<IngestedSource(id={self.id}, profile_id={self.profile_id}, source_type={self.source_type})>"
