"""ShareToken model for time-limited public review sharing."""

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


class ShareToken(Base):
    """Token granting time-limited public read access to a review.

    A share token is generated when a logged-in user clicks "Copy link" on a
    completed review. Anyone who receives the resulting ``/share/<token>`` URL
    can view the review without authenticating. Tokens expire after 30 days.

    If an unexpired token already exists for a review, the same token is
    returned on subsequent share requests. A new token is only generated when
    no active token exists.
    """

    __tablename__ = "share_tokens"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        default=lambda: secrets.token_urlsafe(32),
    )
    review_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    review: Mapped["Review"] = relationship("Review", back_populates="share_tokens")

    __table_args__ = (Index("ix_share_tokens_review_id", "review_id"),)

    def __repr__(self) -> str:
        return (
            f"<ShareToken(id={self.id}, review_id={self.review_id},"
            f" expires_at={self.expires_at})>"
        )
