from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackSection(BaseModel):
    section_name: str
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    suggestions: list[str]


class ReviewCreate(BaseModel):
    profile_id: UUID


class ReviewResponse(BaseModel):
    id: UUID
    profile_id: UUID
    status: str
    sections: list[FeedbackSection] | None
    overall_score: float | None
    error_message: str | None = None
    is_public: bool
    share_expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int


class ShareLinkResponse(BaseModel):
    review_id: UUID
    is_public: bool
    share_url: str
    expires_at: datetime
