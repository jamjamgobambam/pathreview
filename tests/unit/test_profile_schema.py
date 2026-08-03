"""Tests for the profile API response schema.

Covers issue #78
(https://github.com/jamjamgobambam/pathreview/issues/78): the profile response
schema exposed the identifier only as ``id`` and was missing the ``profile_id``
field that clients need to make subsequent requests. These tests assert that
``ProfileResponse`` now exposes ``profile_id`` (mapped from ``id``) while keeping
``id`` for backward compatibility.
"""

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from api.schemas.profile import ProfileResponse


@pytest.mark.unit
class TestProfileResponseSchema:
    """Schema-level tests for ProfileResponse (issue #78)."""

    @pytest.fixture
    def profile_row(self) -> SimpleNamespace:
        """Stand-in for a persisted Profile ORM row.

        Mirrors ``core.models.profile.Profile``: the primary key is stored as
        ``id`` and there is no ``profile_id`` attribute. ``ProfileResponse``
        uses ``from_attributes``, so it reads these attributes directly.
        """
        return SimpleNamespace(
            id=uuid4(),
            user_id=uuid4(),
            github_username="janedoe",
            portfolio_url="https://janedoe.dev",
            created_at=datetime.now(UTC),
            resume_filename="resume.pdf",
        )

    def test_response_includes_profile_id(self, profile_row: SimpleNamespace) -> None:
        """The creation response must expose a ``profile_id`` field (issue #78)."""
        response = ProfileResponse.model_validate(profile_row)
        payload = response.model_dump()

        assert (
            "profile_id" in payload
        ), "ProfileResponse is missing the 'profile_id' field (issue #78)"

    def test_profile_id_matches_id(self, profile_row: SimpleNamespace) -> None:
        """``profile_id`` should carry the same value as the record's ``id``."""
        response = ProfileResponse.model_validate(profile_row)
        payload = response.model_dump()

        assert payload["profile_id"] == profile_row.id
        assert payload["profile_id"] == payload["id"]

    def test_id_field_still_present(self, profile_row: SimpleNamespace) -> None:
        """``id`` must remain in the payload so existing clients don't break."""
        response = ProfileResponse.model_validate(profile_row)
        payload = response.model_dump()

        assert payload["id"] == profile_row.id

    def test_profile_id_serializes_as_uuid_string(self, profile_row: SimpleNamespace) -> None:
        """``profile_id`` must serialize to the same UUID string as ``id``."""
        response = ProfileResponse.model_validate(profile_row)
        payload = json.loads(response.model_dump_json())

        assert payload["profile_id"] == str(profile_row.id)
        assert payload["profile_id"] == payload["id"]

    def test_profile_id_present_when_optional_fields_missing(self) -> None:
        """``profile_id`` is returned even when optional fields are ``None``."""
        row = SimpleNamespace(
            id=uuid4(),
            user_id=uuid4(),
            github_username=None,
            portfolio_url=None,
            created_at=datetime.now(UTC),
            resume_filename=None,
        )

        payload = ProfileResponse.model_validate(row).model_dump()

        assert payload["profile_id"] == row.id
