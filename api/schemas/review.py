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


class ShareTokenResponse(BaseModel):
    """Response returned when an owner generates a public share link."""

    share_token: str
    share_url: str


class PublicReviewResponse(BaseModel):
    """Sanitized review payload exposed through the public share endpoint.

    Deliberately omits owner-identifying fields (``profile_id``,
    ``error_message``) so a shared link never leaks who created the review.
    """

    id: UUID
    status: str
    sections: list[FeedbackSection] | None
    overall_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
