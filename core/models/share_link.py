"""Share link model for public, tokenized access to a review."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.review import Review


class ShareLink(Base):
    """Model for an opaque, expiring token that grants public read-only access to a review."""

    __tablename__ = "share_links"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    review_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    review: Mapped["Review"] = relationship("Review", back_populates="share_links")

    __table_args__ = (
        Index("ix_share_links_review_id", "review_id"),
        Index("ix_share_links_token", "token", unique=True),
        Index("ix_share_links_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ShareLink(id={self.id}, review_id={self.review_id}, expires_at={self.expires_at})>"
        )
