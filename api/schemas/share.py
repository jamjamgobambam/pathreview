from datetime import datetime

from pydantic import BaseModel

from api.schemas.review import FeedbackSection


class ShareLinkResponse(BaseModel):
    """Returned when a share link is minted. The frontend builds the public
    URL as ``${origin}/shared/${token}``; ``expires_at`` lets the UI show when
    the link stops working."""

    token: str
    expires_at: datetime

    model_config = {"from_attributes": True}


class PublicReviewResponse(BaseModel):
    """Read-only, public-safe view of a review served via a share token.

    Deliberately omits owner-linking and internal fields (id, profile_id,
    status, error_message) so an anonymous viewer only sees the review
    summary itself.
    """

    overall_score: float | None
    sections: list[FeedbackSection] | None
    created_at: datetime

    model_config = {"from_attributes": True}
