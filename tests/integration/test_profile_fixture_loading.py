"""Integration test for the shared sample profile fixture (issue #106).

Restores coverage that was lost when
``tests/fixtures/sample_profiles/basic_profile.json`` went missing. The
fixture is loaded from disk and mapped onto real ``Profile`` and
``IngestedSource`` ORM objects to verify the one-to-many relationship wiring
holds — the repos in the JSON become ``IngestedSource`` rows linked back to a
single ``Profile``.

No database service is required: SQLAlchemy populates ``back_populates``
collections on attribute assignment for transient (un-persisted) objects, so
this exercises the real model relationships without a live connection.
"""

import json
from pathlib import Path
from typing import Any

import pytest

# Import from the package so the full mapper registry (User, Profile,
# IngestedSource, Review) is configured before we build related objects.
from core.models import IngestedSource, Profile

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "sample_profiles" / "basic_profile.json"


@pytest.fixture
def basic_profile_data() -> dict[str, Any]:
    """Load the shared sample profile fixture from disk."""
    with FIXTURE_PATH.open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


def _build_profile(data: dict) -> Profile:
    """Construct a Profile and its repo IngestedSource rows from fixture data."""
    profile = Profile(
        github_username=data["github_username"],
        resume_filename=data["resume_filename"],
        resume_text=data["resume_text"],
        portfolio_url=data["portfolio_url"],
    )
    for repo in data["repos"]:
        IngestedSource(
            source_type=repo["source_type"],
            source_url=repo["source_url"],
            filename=repo["filename"],
            profile=profile,
        )
    return profile


@pytest.mark.integration
class TestProfileFixtureLoading:
    """Build real ORM objects from the JSON fixture and assert the graph."""

    def test_fixture_file_exists(self) -> None:
        assert FIXTURE_PATH.exists(), f"Missing sample profile fixture: {FIXTURE_PATH}"

    def test_profile_fields_populated(self, basic_profile_data: dict) -> None:
        profile = _build_profile(basic_profile_data)

        assert profile.github_username == "janedoe"
        assert profile.resume_filename == "jane_doe_resume.pdf"
        assert profile.resume_text and "Jane Doe" in profile.resume_text
        assert profile.portfolio_url.startswith("https://")

    def test_repos_map_to_two_ingested_sources(self, basic_profile_data: dict) -> None:
        profile = _build_profile(basic_profile_data)

        # The one-to-many relationship is populated purely from setting
        # ``profile=`` on each IngestedSource (back_populates).
        assert len(profile.ingested_sources) == 2
        assert all(src.source_type == "repo" for src in profile.ingested_sources)
        assert all(src.profile is profile for src in profile.ingested_sources)

        urls = {src.source_url for src in profile.ingested_sources}
        assert urls == {
            "https://github.com/janedoe/weather-app",
            "https://github.com/janedoe/portfolio-tracker",
        }
