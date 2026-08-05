from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _validate_portfolio_url(value: str | None) -> str | None:
    """Ensure a portfolio URL, if provided, is a well-formed http(s) URL."""
    if value is None:
        return value
    value = value.strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("portfolio_url must be a valid http or https URL")
    return value


class ProfileCreate(BaseModel):
    github_username: str | None = Field(default=None, max_length=255)
    portfolio_url: str | None = Field(default=None, max_length=500)

    _validate_portfolio_url = field_validator("portfolio_url")(_validate_portfolio_url)


class ProfileUpdate(BaseModel):
    github_username: str | None = Field(default=None, max_length=255)
    portfolio_url: str | None = Field(default=None, max_length=500)

    _validate_portfolio_url = field_validator("portfolio_url")(_validate_portfolio_url)


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    github_username: str | None
    portfolio_url: str | None
    created_at: datetime
    resume_filename: str | None

    model_config = {"from_attributes": True}
