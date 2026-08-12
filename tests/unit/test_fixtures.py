"""Tests for shared test fixtures defined in tests/conftest.py."""

import pytest


@pytest.mark.unit
def test_sample_profile_data_has_expected_shape(sample_profile_data: dict) -> None:
    """sample_profile_data fixture should load with expected top-level keys."""
    assert sample_profile_data["github_username"]
    assert sample_profile_data["resume_text"]
    assert len(sample_profile_data["repos"]) == 2
    for repo in sample_profile_data["repos"]:
        assert repo["name"]
        assert repo["html_url"]
        assert repo["readme_content"]
