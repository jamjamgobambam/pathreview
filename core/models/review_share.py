"""ReviewShare model for storing public review share tokens."""

import secrets
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.review import Review


class ReviewShare(Base):
    """Model for storing time-limited public share tokens for reviews."""

    __tablename__ = "review_shares"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    review_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    share_token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        default=lambda: secrets.token_urlsafe(32),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    review: Mapped["Review"] = relationship("Review", back_populates="shares")

    __table_args__ = (
        Index("ix_review_shares_share_token", "share_token"),
        Index("ix_review_shares_review_id", "review_id"),
    )
