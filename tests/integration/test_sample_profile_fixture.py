"""Integration tests for the shared sample portfolio fixture.

These tests exercise ``tests/fixtures/sample_profiles/basic_profile.json``
through the ingestion parsers to guarantee the fixture stays realistic and
pipeline-compatible. They are skipped (in effect, they error) whenever the
fixture is missing — which is the state issue #106 is about.
"""

from typing import Any

import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.repo_analyzer import RepoAnalyzer
from ingestion.parsers.resume_parser import ResumeParser


@pytest.mark.integration
class TestSampleProfileFixture:
    """Validate the shared sample portfolio fixture end to end."""

    def test_fixture_has_required_portfolio_fields(self, basic_profile: dict[str, Any]) -> None:
        """The fixture must describe a GitHub username, resume, and two repos."""
        assert basic_profile["github_username"]
        assert basic_profile["resume_text"].strip()
        assert basic_profile["portfolio_url"]

        repos = basic_profile["repositories"]
        assert isinstance(repos, list)
        assert len(repos) == 2

    def test_repositories_parse_through_repo_analyzer(self, basic_profile: dict[str, Any]) -> None:
        """Each repo entry should be shaped like the GitHub API dict RepoAnalyzer reads."""
        analyzer = RepoAnalyzer()

        for repo in basic_profile["repositories"]:
            result = analyzer.parse(repo)

            assert isinstance(result, ParseResult)
            assert result.source_type == "repo"
            assert result.metadata["repo_name"] == repo["name"]
            assert result.metadata["primary_language"] == repo["language"]

    def test_resume_parses_through_resume_parser(self, basic_profile: dict[str, Any]) -> None:
        """The fixture's resume_text should parse into recognizable sections."""
        result = ResumeParser().parse(basic_profile["resume_text"])

        assert isinstance(result, ParseResult)
        assert result.source_type == "resume"
        detected = [s.lower() for s in result.metadata["detected_sections"]]
        assert any("experience" in s for s in detected) or any("skills" in s for s in detected)
