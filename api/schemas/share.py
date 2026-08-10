from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from api.schemas.review import FeedbackSection


class ShareTokenResponse(BaseModel):
    token: str
    share_url: str  # full public URL e.g. https://app/share/<token>
    expires_at: datetime


class PublicReviewResponse(BaseModel):
    """Read-only review data returned on the public share page."""

    id: UUID
    overall_score: float | None
    sections: list[FeedbackSection] | None
    created_at: datetime

    model_config = {"from_attributes": True}
