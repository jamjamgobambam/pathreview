from datetime import datetime

from pydantic import BaseModel


class ShareLinkResponse(BaseModel):
    """Returned when a share link is minted. The frontend builds the public
    URL as ``${origin}/shared/${token}``; ``expires_at`` lets the UI show when
    the link stops working."""

    token: str
    expires_at: datetime

    model_config = {"from_attributes": True}
