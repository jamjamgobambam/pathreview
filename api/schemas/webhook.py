from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class CallbackCreate(BaseModel):
    profile_id: UUID
    url: HttpUrl


class CallbackResponse(BaseModel):
    id: UUID
    user_id: UUID
    profile_id: UUID
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: UUID
    callback_id: UUID
    review_id: UUID
    delivery_status: str
    created_at: datetime
    last_sent_at: datetime | None
    last_ack_at: datetime | None

    model_config = {"from_attributes": True}
