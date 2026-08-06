"""Integration coverage for the shared sample profile fixture.

The fixture at ``tests/fixtures/sample_profiles/basic_profile.json`` is shared
test data for profile, resume, and repository ingestion flows. These assertions
keep the fixture well-formed and make the expected contract explicit.
"""

import json
from pathlib import Path

import pytest

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "sample_profiles" / "basic_profile.json"
)
PROFILE_REQUIRED_KEYS = {
    "github_username",
    "portfolio_url",
    "resume_filename",
    "resume_text",
    "repositories",
}
REPOSITORY_REQUIRED_KEYS = {
    "name",
    "description",
    "html_url",
    "language",
    "stargazers_count",
    "forks_count",
    "open_issues_count",
    "pushed_at",
    "readme_content",
    "file_structure",
}


@pytest.mark.integration
def test_sample_profile_fixture_exists() -> None:
    """The shared sample-profile fixture should exist on disk."""
    assert FIXTURE_PATH.is_file(), (
        f"Expected sample profile fixture at {FIXTURE_PATH}, but it is missing. "
        "Restore it with a realistic sample portfolio (issue #106)."
    )


@pytest.mark.integration
def test_sample_profile_fixture_has_expected_shape() -> None:
    """The fixture should load as JSON and carry the fields the issue names."""
    with FIXTURE_PATH.open(encoding="utf-8") as f:
        profile = json.load(f)

    assert isinstance(profile, dict), "fixture should be a JSON object"
    assert profile.keys() >= PROFILE_REQUIRED_KEYS
    assert profile["github_username"] == "janedoe"
    assert profile["resume_filename"].endswith(".pdf")
    assert "Technical Skills" in profile["resume_text"]

    repos = profile.get("repositories")
    assert (
        isinstance(repos, list) and len(repos) == 2
    ), "fixture should include exactly two repositories"

    for repo in repos:
        assert repo.keys() >= REPOSITORY_REQUIRED_KEYS
        assert repo["html_url"].startswith("https://github.com/janedoe/")
        assert repo["readme_content"].startswith("# ")
        assert isinstance(repo["file_structure"], list)
        assert repo["file_structure"], "repository fixture should include files"
