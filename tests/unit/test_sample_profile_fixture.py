"""Tests for the shared basic_profile sample portfolio fixture."""

from datetime import datetime
from uuid import UUID

import pytest

from core.models.profile import Profile

# Fields each repo entry must expose so it can be fed to
# agent/tools/github_tool.py or serialized into IngestedSource.raw_data.
EXPECTED_REPO_FIELDS = {"name", "description", "language", "url", "readme_text"}


@pytest.mark.unit
class TestSampleUserProfileFixture:
    """Test suite for the sample_user_profile fixture."""

    def test_fixture_loads_with_profile_and_repos(self, sample_user_profile):
        """Test the fixture loads and exposes both top-level sections."""
        assert isinstance(sample_user_profile, dict)
        assert set(sample_user_profile) == {"profile", "repos"}
        assert isinstance(sample_user_profile["profile"], dict)
        assert isinstance(sample_user_profile["repos"], list)

    def test_profile_keys_match_profile_model_columns(self, sample_user_profile):
        """Test the profile section stays in sync with the Profile model columns."""
        model_columns = {column.name for column in Profile.__table__.columns}

        assert set(sample_user_profile["profile"]) == model_columns

    def test_profile_values_are_populated(self, sample_user_profile):
        """Test every profile field carries real sample content, not None."""
        profile = sample_user_profile["profile"]

        for field, value in profile.items():
            assert value, f"profile field {field!r} is empty"

    def test_profile_ids_are_valid_uuids(self, sample_user_profile):
        """Test id and user_id parse as UUIDs, matching the model's UUID columns."""
        profile = sample_user_profile["profile"]

        assert UUID(profile["id"])
        assert UUID(profile["user_id"])

    def test_profile_strings_respect_model_length_limits(self, sample_user_profile):
        """Test string fields fit the column lengths declared on the model."""
        profile = sample_user_profile["profile"]

        assert len(profile["github_username"]) <= 255
        assert len(profile["resume_filename"]) <= 255
        assert len(profile["portfolio_url"]) <= 500

    def test_profile_timestamps_are_timezone_aware(self, sample_user_profile):
        """Test timestamps parse as ISO 8601 with a timezone, per DateTime(timezone=True)."""
        profile = sample_user_profile["profile"]

        for field in ("created_at", "updated_at"):
            parsed = datetime.fromisoformat(profile[field])
            assert parsed.tzinfo is not None, f"{field} is not timezone-aware"

    def test_fixture_has_two_repos(self, sample_user_profile):
        """Test the fixture supplies the two repos the issue calls for."""
        assert len(sample_user_profile["repos"]) == 2

    def test_repos_expose_fields_github_tool_consumes(self, sample_user_profile):
        """Test each repo carries the fields downstream tooling reads."""
        for repo in sample_user_profile["repos"]:
            assert set(repo) == EXPECTED_REPO_FIELDS
            for field, value in repo.items():
                assert value, f"repo field {field!r} is empty"

    def test_repo_names_are_unique(self, sample_user_profile):
        """Test repo names are distinct so they can be used as lookup keys."""
        names = [repo["name"] for repo in sample_user_profile["repos"]]

        assert len(set(names)) == len(names)
