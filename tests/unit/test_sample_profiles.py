"""Unit tests for the shared sample portfolio fixture (basic_profile.json).

These validate the *structure* of the fixture so a future edit that breaks its
schema is caught by ``make test-unit``. The end-to-end behaviour (feeding the
fixture through the ingestion parsers) is covered separately by
``tests/integration/test_sample_profile_fixture.py``.
"""

from typing import Any

import pytest


@pytest.mark.unit
class TestBasicProfileFixture:
    """Validate the structure of the basic_profile.json fixture."""

    def test_has_required_top_level_fields(self, basic_profile: dict[str, Any]) -> None:
        """The fixture exposes a GitHub username, resume text, and portfolio URL."""
        assert isinstance(basic_profile["github_username"], str)
        assert basic_profile["github_username"]
        assert isinstance(basic_profile["resume_text"], str)
        assert basic_profile["resume_text"].strip()
        assert isinstance(basic_profile["portfolio_url"], str)
        assert basic_profile["portfolio_url"].startswith("http")

    def test_has_exactly_two_repositories(self, basic_profile: dict[str, Any]) -> None:
        """The fixture describes exactly two repositories, per issue #106."""
        repos = basic_profile["repositories"]
        assert isinstance(repos, list)
        assert len(repos) == 2

    def test_repositories_expose_github_api_fields(self, basic_profile: dict[str, Any]) -> None:
        """Each repo carries the GitHub-API fields the ingestion parsers read."""
        required_fields: dict[str, type] = {
            "name": str,
            "description": str,
            "language": str,
            "stargazers_count": int,
            "forks_count": int,
            "open_issues_count": int,
            "pushed_at": str,
            "html_url": str,
            "readme_content": str,
        }
        for repo in basic_profile["repositories"]:
            for field, field_type in required_fields.items():
                assert field in repo, f"repo is missing field: {field}"
                assert isinstance(repo[field], field_type)
