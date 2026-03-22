from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List


class FeedbackSection(BaseModel):
    section_name: str
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    suggestions: List[str]


class ReviewCreate(BaseModel):
    profile_id: UUID


class ReviewResponse(BaseModel):
    id: UUID
    profile_id: UUID
    status: str
    sections: Optional[List[FeedbackSection]]
    overall_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    items: List[ReviewResponse]
    total: int
    page: int
    page_size: int
