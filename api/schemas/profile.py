from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    github_username: str | None = Field(default=None, max_length=255)
    portfolio_url: str | None = Field(default=None, max_length=500)


class ProfileUpdate(BaseModel):
    github_username: str | None = Field(default=None, max_length=255)
    portfolio_url: str | None = Field(default=None, max_length=500)


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    github_username: str | None
    portfolio_url: str | None
    created_at: datetime
    resume_filename: str | None

    model_config = {"from_attributes": True}
