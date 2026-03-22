"""Review model for storing portfolio review results."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.profile import Profile


class Review(Base):
    """Model for storing portfolio review results and analysis."""

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    profile_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # "pending", "processing", "complete", "failed"
    sections: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Structured review output
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="reviews")

    __table_args__ = (
        Index("ix_reviews_profile_id", "profile_id"),
        Index("ix_reviews_status", "status"),
        Index("ix_reviews_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, profile_id={self.profile_id}, status={self.status})>"
