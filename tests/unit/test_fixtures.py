"""Tests for testing fixtures presence and structure."""

import json
import os

import pytest


@pytest.mark.unit
def test_basic_profile_fixture_exists_and_is_valid() -> None:
    """Verify that basic_profile.json exists and is valid JSON with expected keys."""
    fixture_path = os.path.join("tests", "fixtures", "sample_profiles", "basic_profile.json")

    # 1. Verify existence
    assert os.path.exists(fixture_path), f"Fixture not found at {fixture_path}"

    # 2. Verify validity and keys
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)

    assert "github_username" in data, "Missing github_username"
    assert "resume" in data, "Missing resume"
    assert "repositories" in data, "Missing repositories"

    # 3. Verify repositories structure
    repos = data["repositories"]
    assert isinstance(repos, list), "repositories must be a list"
    assert len(repos) >= 2, "repositories must contain at least two entries"

    for repo in repos:
        assert "name" in repo, "Missing repo name"
        assert "description" in repo, "Missing repo description"
        assert "language" in repo, "Missing repo language"
        assert "readme_content" in repo, "Missing repo readme_content"
        assert "file_structure" in repo, "Missing repo file_structure"
