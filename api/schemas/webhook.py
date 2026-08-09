"""Schemas for webhook API requests and responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


def _parse_events(value: str | list[str] | None) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return [event.strip() for event in value.split(",") if event.strip()]
    if isinstance(value, list):
        parsed: list[str] = []
        for item in value:
            if isinstance(item, str):
                parsed.extend([event.strip() for event in item.split(",") if event.strip()])
            elif item is not None:
                parsed.append(str(item).strip())
        return parsed
    raise TypeError("events must be a string or list of strings")


class WebhookCreate(BaseModel):
    """Schema for creating a new webhook."""

    url: HttpUrl = Field(..., description="Webhook callback URL")
    events: list[str] = Field(
        default_factory=lambda: ["review.completed"],
        description="List of events to listen for",
    )
    secret: Optional[str] = Field(
        default=None, description="Optional secret for HMAC signature verification"
    )
    description: Optional[str] = Field(
        default=None, description="Optional description of the webhook"
    )

    @field_validator("events", mode="before")
    def validate_events(cls, value):
        parsed = _parse_events(value)
        return parsed if parsed is not None else ["review.completed"]


class WebhookUpdate(BaseModel):
    """Schema for updating an existing webhook."""

    url: Optional[HttpUrl] = Field(default=None, description="New webhook callback URL")
    events: Optional[list[str]] = Field(
        default=None,
        description="New list of events or comma-separated event string",
    )
    secret: Optional[str] = Field(
        default=None, description="New secret for HMAC signature verification"
    )

    @field_validator("events", mode="before")
    def validate_events(cls, value):
        return _parse_events(value)
    description: Optional[str] = Field(default=None, description="New description")
    is_active: Optional[bool] = Field(default=None, description="New active status")


class WebhookResponse(BaseModel):
    """Schema for webhook responses."""

    id: UUID
    url: HttpUrl
    events: list[str]
    is_active: bool
    secret: Optional[str] = None
    description: Optional[str] = None
    last_triggered_at: Optional[datetime] = None
    last_status_code: Optional[int] = None
    failure_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("events", mode="before")
    def validate_events(cls, value):
        return _parse_events(value)


class WebhookListResponse(BaseModel):
    """Schema for webhook list responses."""

    items: list[WebhookResponse]
    total: int
    page: int
    page_size: int


class WebhookEventPayload(BaseModel):
    """Schema for webhook event payload sent to callback URL."""

    event: str = Field(..., description="Event name")
    webhook_id: str = Field(..., description="Webhook ID")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    data: dict = Field(..., description="Event-specific data")
