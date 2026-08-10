"""Webhook delivery audit log model."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.webhook import Webhook


class WebhookDelivery(Base):
    """Tracks each outbound webhook delivery attempt for a review."""

    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    webhook_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    review_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    attempt_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_status_code: Mapped[int | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    webhook: Mapped["Webhook"] = relationship("Webhook", back_populates="deliveries")

    __table_args__ = (
        Index("ix_webhook_deliveries_webhook_id", "webhook_id"),
        Index("ix_webhook_deliveries_review_id", "review_id"),
        Index("ix_webhook_deliveries_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<WebhookDelivery(id={self.id}, webhook_id={self.webhook_id}, review_id={self.review_id}, status={self.status})>"
