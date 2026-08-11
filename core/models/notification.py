"""Notification model for tracking webhook delivery attempts for completed reviews."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.callback import Callback


class Notification(Base):
    """Model for tracking a single webhook notification's delivery status.

    The id is a deterministic value derived from (user_id, profile_id, review_id) rather than a
    random uuid4, so retries and resends for the same completion event reuse the same row.
    """

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    callback_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("callbacks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    review_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivery_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="retry"
    )  # "success", "fail", "retry"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_ack_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    callback: Mapped["Callback"] = relationship("Callback", back_populates="notifications")

    def __repr__(self) -> str:
        return (
            f"<Notification(id={self.id}, review_id={self.review_id}, "
            f"delivery_status={self.delivery_status})>"
        )
