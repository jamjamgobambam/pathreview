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
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int


class ShareLinkResponse(BaseModel):
    """Response returned when a share link is created for a review."""

    token: str
    expires_at: datetime

    model_config = {"from_attributes": True}


class SharedReviewResponse(BaseModel):
    """Public, read-only view of a review served via a share token.

    Deliberately omits ownership fields (``id``, ``profile_id``) so a public
    link exposes only the summary itself.
    """

    overall_score: float | None
    sections: list[FeedbackSection] | None
    created_at: datetime
    expires_at: datetime
