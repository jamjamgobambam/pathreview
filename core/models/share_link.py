"""ShareLink model for storing public, expiring review share tokens."""

from datetime import datetime, timedelta
from secrets import token_urlsafe
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.review import Review

SHARE_LINK_TTL_DAYS = 30


def _default_expiry() -> datetime:
    return datetime.utcnow() + timedelta(days=SHARE_LINK_TTL_DAYS)


class ShareLink(Base):
    """Model for storing public share tokens that grant read-only access to a review."""

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
    token: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, default=lambda: token_urlsafe(32)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_default_expiry
    )

    # Relationships
    review: Mapped["Review"] = relationship("Review")

    __table_args__ = (
        Index("ix_share_links_token", "token", unique=True),
        Index("ix_share_links_review_id", "review_id"),
    )

    def is_expired(self) -> bool:
        return bool(datetime.utcnow() >= self.expires_at)

    def __repr__(self) -> str:
        return (
            f"<ShareLink(id={self.id}, review_id={self.review_id}, expires_at={self.expires_at})>"
        )
