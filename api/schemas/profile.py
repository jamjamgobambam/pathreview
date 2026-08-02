from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _validate_portfolio_url(value: str | None) -> str | None:
    """Reject portfolio URLs that are not http(s), so bad input fails early."""
    if value is None or value == "":
        return value
    if not value.startswith(("http://", "https://")):
        raise ValueError("portfolio_url must start with http:// or https://")
    return value


class ProfileCreate(BaseModel):
    github_username: str | None = Field(default=None, max_length=255)
    portfolio_url: str | None = Field(default=None, max_length=500)

    _check_portfolio_url = field_validator("portfolio_url")(_validate_portfolio_url)


class ProfileUpdate(BaseModel):
    github_username: str | None = Field(default=None, max_length=255)
    portfolio_url: str | None = Field(default=None, max_length=500)

    _check_portfolio_url = field_validator("portfolio_url")(_validate_portfolio_url)


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    github_username: str | None
    portfolio_url: str | None
    created_at: datetime
    resume_filename: str | None

    model_config = {"from_attributes": True}
