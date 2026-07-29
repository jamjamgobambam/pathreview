"""Reproduction test for issue #106.

The shared sample-profile fixture at
``tests/fixtures/sample_profiles/basic_profile.json`` was deleted. Integration
tests that expect a realistic sample portfolio can no longer load it.

This test documents the broken behavior: it asserts the fixture exists and can
be parsed as a JSON object with the fields the issue describes (a GitHub
username, resume information, and two repositories). It FAILS on the current
codebase because the file is missing, and will PASS once the fixture is
restored in the implementation step.
"""

import json
from pathlib import Path

import pytest

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "sample_profiles" / "basic_profile.json"
)


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
    assert profile.get("github_username"), "fixture should include a github_username"

    repos = profile.get("repositories")
    assert (
        isinstance(repos, list) and len(repos) == 2
    ), "fixture should include exactly two repositories"
