"""Regression tests for JavaScript and TypeScript skill detection."""

import pytest

from ingestion.parsers.skill_extractor import SkillExtractor


@pytest.fixture
def extractor() -> SkillExtractor:
    """Create a skill extractor for each test."""
    return SkillExtractor()


@pytest.mark.unit
def test_javascript_require_call_without_filename(
    extractor: SkillExtractor,
) -> None:
    """Detect JavaScript from require() without filename evidence."""
    result = extractor.extract_skills('require("fs");')

    assert any(skill.name == "JavaScript" for skill in result)
