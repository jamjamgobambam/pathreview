from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field


class WebhookCreate(BaseModel):
    url: AnyHttpUrl = Field(..., description="Callback URL for review notifications")


class WebhookResponse(BaseModel):
    id: UUID
    url: AnyHttpUrl
    is_active: bool
    created_at: datetime
    updated_at: datetime
    secret: str | None = None

    model_config = {"from_attributes": True}
