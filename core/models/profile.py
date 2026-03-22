"""Profile model for storing portfolio and review information."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Profile(Base):
    """Profile model for storing user portfolio information."""

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    github_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profiles")
    ingested_sources: Mapped[list["IngestedSource"]] = relationship("IngestedSource", back_populates="profile", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="profile", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_profiles_user_id", "user_id"),
        Index("ix_profiles_github_username", "github_username"),
    )

    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, user_id={self.user_id}, github_username={self.github_username})>"
