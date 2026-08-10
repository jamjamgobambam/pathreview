"""ShareLink model for public, time-limited review share links."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.review import Review


class ShareLink(Base):
    """A public, expiring link to a read-only view of a review.

    The ``token`` is the value embedded in the shareable URL and is the only
    identifier needed, so it doubles as the primary key. A link stops working
    once ``expires_at`` has passed (30 days after creation).
    """

    __tablename__ = "share_links"

    token: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
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

    # One-directional link to the review; no back_populates needed on Review.
    review: Mapped["Review"] = relationship("Review")

    def __repr__(self) -> str:
        return f"<ShareLink(token={self.token}, review_id={self.review_id})>"
