"""Tests for the basic_profile.json sample portfolio fixture.

These tests load the fixture from disk and feed its data through the real
ResumeParser and RepoAnalyzer, proving the fixture is valid and usable. If
the fixture is ever deleted or malformed again, these tests fail loudly.
"""

import json
from pathlib import Path

import pytest

from ingestion.parsers.repo_analyzer import RepoAnalyzer
from ingestion.parsers.resume_parser import ResumeParser

# Path to the fixture, built relative to THIS test file so it works anywhere.
# __file__ is this file; .parent is tests/unit, .parent.parent is tests/.
FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "sample_profiles" / "basic_profile.json"


@pytest.mark.unit
class TestBasicProfileFixture:
    """Verify the sample portfolio fixture loads and feeds the parsers."""

    @pytest.fixture
    def profile(self) -> dict:
        """Load and return the sample portfolio fixture as a dict."""
        data: dict = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        return data

    def test_fixture_file_exists(self) -> None:
        """The fixture file must exist at the expected path."""
        assert FIXTURE_PATH.exists()

    def test_has_required_top_level_keys(self, profile: dict) -> None:
        """The profile must expose a username, resume text, and two repos."""
        assert isinstance(profile["github_username"], str)
        assert profile["github_username"]
        assert isinstance(profile["resume_text"], str)
        assert profile["resume_text"]
        assert isinstance(profile["repositories"], list)
        assert len(profile["repositories"]) == 2

    def test_resume_text_feeds_resume_parser(self, profile: dict) -> None:
        """The resume text should parse and expose recognizable sections."""
        result = ResumeParser().parse(profile["resume_text"])

        assert result.source_type == "resume"
        detected = [s.lower() for s in result.metadata["detected_sections"]]
        assert "skills" in detected
        assert "experience" in detected

    def test_python_repo_is_analyzed(self, profile: dict) -> None:
        """The first repo (Python) should be detected with tests and CI."""
        repo = profile["repositories"][0]
        result = RepoAnalyzer().parse(repo)

        assert result.metadata["primary_language"] == "Python"
        assert result.metadata["has_tests"] is True
        assert result.metadata["has_ci"] is True
        tech_stack = [t.lower() for t in result.metadata["tech_stack"]]
        assert "python" in tech_stack

    def test_typescript_repo_is_analyzed(self, profile: dict) -> None:
        """The second repo (TypeScript) should be detected without tests/CI."""
        repo = profile["repositories"][1]
        result = RepoAnalyzer().parse(repo)

        assert result.metadata["primary_language"] == "TypeScript"
        assert result.metadata["has_tests"] is False
        assert result.metadata["has_ci"] is False
        tech_stack = [t.lower() for t in result.metadata["tech_stack"]]
        assert "typescript" in tech_stack
