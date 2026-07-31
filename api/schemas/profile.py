from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional


def _validate_portfolio_url(value: str | None) -> str | None:
    if value is None or value == "":
        return value
    if not value.startswith(("http://", "https://")):
        raise ValueError("portfolio_url must start with http:// or https://")
    return value


class ProfileCreate(BaseModel):
    github_username: Optional[str] = Field(default=None, max_length=255)
    portfolio_url: Optional[str] = Field(default=None, max_length=500)

    _validate_portfolio_url = field_validator("portfolio_url")(_validate_portfolio_url)


class ProfileUpdate(BaseModel):
    github_username: Optional[str] = Field(default=None, max_length=255)
    portfolio_url: Optional[str] = Field(default=None, max_length=500)

    _validate_portfolio_url = field_validator("portfolio_url")(_validate_portfolio_url)


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    github_username: Optional[str]
    portfolio_url: Optional[str]
    created_at: datetime
    resume_filename: Optional[str]

    model_config = {"from_attributes": True}
