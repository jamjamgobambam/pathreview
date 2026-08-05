"""ShareLink model for public, expiring review share links."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.review import Review


class ShareLink(Base):
    """A public, expiring link that grants read-only access to a review summary.

    Each row maps an unguessable ``token`` to a review. Anyone holding the token
    can read the review summary without authenticating, until ``expires_at``.
    """

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
    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    review: Mapped["Review"] = relationship("Review", back_populates="share_links")

    def __repr__(self) -> str:
        return (
            f"<ShareLink(id={self.id}, review_id={self.review_id}, expires_at={self.expires_at})>"
        )
