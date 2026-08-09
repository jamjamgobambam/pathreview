"""
Reproduction test for issue #106.

Demonstrates that tests/fixtures/sample_profiles/basic_profile.json is missing.
These tests will FAIL until the fixture file is restored.
"""

import json
from pathlib import Path

import pytest

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "sample_profiles" / "basic_profile.json"


@pytest.mark.integration
class TestSharedProfileFixture:
    """Verify the shared profile fixture exists and has the expected shape."""

    def test_basic_profile_fixture_file_exists(self) -> None:
        """
        Fails when tests/fixtures/sample_profiles/basic_profile.json is absent.

        Root cause: the fixture was deleted and never restored.  Any test that
        builds a sample profile from this file will either skip or crash.
        """
        assert FIXTURE_PATH.exists(), (
            f"Missing fixture file: {FIXTURE_PATH}\n"
            "Restore it at tests/fixtures/sample_profiles/basic_profile.json "
            "with a realistic sample portfolio (github_username, resume_text, two repos)."
        )

    def test_basic_profile_fixture_is_valid_json(self) -> None:
        """Fixture must be parseable JSON before any test can consume it."""
        if not FIXTURE_PATH.exists():
            pytest.skip(
                "Skipped: fixture file missing (see test_basic_profile_fixture_file_exists)"
            )
        with FIXTURE_PATH.open() as f:
            data = json.load(f)
        assert isinstance(data, dict), "Fixture root must be a JSON object"

    def test_basic_profile_fixture_has_required_fields(self) -> None:
        """Fixture must contain the fields that integration tests depend on."""
        if not FIXTURE_PATH.exists():
            pytest.skip(
                "Skipped: fixture file missing (see test_basic_profile_fixture_file_exists)"
            )
        with FIXTURE_PATH.open() as f:
            data = json.load(f)

        required_fields = ["github_username", "resume_text", "repos"]
        for field in required_fields:
            assert field in data, f"Fixture is missing required field: '{field}'"

        assert len(data["repos"]) >= 2, "Fixture must include at least two sample repos"
