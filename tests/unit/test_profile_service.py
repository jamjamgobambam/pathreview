"""Tests for profile_service.py"""

from unittest.mock import Mock

import pytest

from core.services.profile_service import profile_has_ingested_content


@pytest.mark.unit
class TestProfileHasIngestedContent:
    """Test suite for profile_has_ingested_content."""

    @pytest.mark.parametrize(
        ("github_username", "portfolio_url", "resume_text", "expected"),
        [
            (None, None, None, False),
            ("", "", "", False),
            ("   ", None, None, False),
            (None, " \n\t ", "", False),
            ("octocat", None, None, True),
            (None, "https://me.dev", None, True),
            (None, None, "Jane Doe\nSoftware Engineer", True),
            ("octocat", "https://me.dev", "resume text", True),
        ],
    )
    def test_detects_reviewable_content(
        self,
        github_username: str | None,
        portfolio_url: str | None,
        resume_text: str | None,
        expected: bool,
    ) -> None:
        """A profile counts as reviewable only with at least one non-blank source."""
        profile = Mock()
        profile.github_username = github_username
        profile.portfolio_url = portfolio_url
        profile.resume_text = resume_text

        assert profile_has_ingested_content(profile) is expected
