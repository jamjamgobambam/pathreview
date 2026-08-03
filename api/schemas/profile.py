from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, computed_field


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

    @computed_field  # type: ignore[misc, prop-decorator]
    @property
    def profile_id(self) -> UUID:
        """Return the profile identifier under the name clients expect.

        The database model stores the primary key as ``id``, but API clients
        rely on a ``profile_id`` field for subsequent requests (for example
        ``GET /profiles/{profile_id}``). This exposes the same value under that
        name while keeping ``id`` for backward compatibility.
        """
        return self.id
