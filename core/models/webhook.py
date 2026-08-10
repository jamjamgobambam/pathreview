"""Webhook model for tracking callback registrations."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.user import User
    from core.models.webhook_delivery import WebhookDelivery


class Webhook(Base):
    """A user-managed callback URL for review notifications."""

    __tablename__ = "webhooks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="webhooks")
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_webhooks_user_id", "user_id"),
        Index("ix_webhooks_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Webhook(id={self.id}, user_id={self.user_id}, url={self.url})>"
