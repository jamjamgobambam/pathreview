"""Webhook model for storing webhook configurations and event registrations."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.user import User


class Webhook(Base):
    """Model for storing webhook configurations and event registrations."""

    __tablename__ = "webhooks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    events: Mapped[str] = mapped_column(
        String(255), nullable=False, default="review.completed"
    )  # Comma-separated list of events: "review.completed", "review.failed"
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    secret: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # For HMAC signature verification
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_status_code: Mapped[int | None] = mapped_column(nullable=True)
    failure_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="webhooks")

    __table_args__ = (
        Index("ix_webhooks_user_id", "user_id"),
        Index("ix_webhooks_is_active", "is_active"),
    )

    def __init__(self, **kwargs):
        if "is_active" not in kwargs:
            kwargs["is_active"] = True
        if "failure_count" not in kwargs:
            kwargs["failure_count"] = 0
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Webhook(id={self.id}, user_id={self.user_id}, url={self.url})>"

    def has_event(self, event: str) -> bool:
        """Check if this webhook is listening for a specific event."""
        return event in self.events.split(",")
