"""Tests for the shared basic sample profile fixture."""

import json
from pathlib import Path

import pytest

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "sample_profiles" / "basic_profile.json"
)
REQUIRED_REPOSITORY_FIELDS = {
    "name",
    "url",
    "description",
    "primary_language",
    "readme",
}


@pytest.mark.unit
def test_basic_profile_fixture_has_expected_shape() -> None:
    """Verify the shared profile is complete, deterministic, and reusable."""
    profile = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert isinstance(profile, dict)
    assert isinstance(profile.get("github_username"), str)
    assert profile["github_username"].strip()

    resume = profile.get("resume")
    assert isinstance(resume, dict)
    assert set(resume) == {"filename", "text"}
    assert all(isinstance(resume[field], str) for field in ("filename", "text"))
    assert all(resume[field].strip() for field in ("filename", "text"))

    repositories = profile.get("repositories")
    assert isinstance(repositories, list)
    assert len(repositories) == 2

    for repository in repositories:
        assert isinstance(repository, dict)
        assert set(repository) == REQUIRED_REPOSITORY_FIELDS
        assert all(isinstance(value, str) for value in repository.values())
        assert all(value.strip() for value in repository.values())

    repository_names = [repository["name"] for repository in repositories]
    assert len(repository_names) == len(set(repository_names))
