"""Tests for the tone-check retry wiring in ReviewGenerator.generate_section (issue #69)."""

from unittest.mock import MagicMock, patch

from rag.generator.output_parser import FeedbackSection
from rag.generator.review_generator import ReviewConfig, ReviewGenerator
from safety.content_filter import ToneCheckResult


def _make_config() -> ReviewConfig:
    return ReviewConfig(
        api_key="test-key",
        base_url="https://example.invalid/v1",
        model="test-model",
    )


def _make_section(content: str = "some feedback") -> FeedbackSection:
    return FeedbackSection(
        section_name="skills_feedback",
        content=content,
        confidence=0.9,
        suggestions=[],
    )


@patch("rag.generator.review_generator.openai.OpenAI")
def test_generate_section_returns_first_attempt_when_constructive(mock_openai: MagicMock) -> None:
    """If the first generation passes the tone check, no retry should happen."""
    generator = ReviewGenerator(_make_config())
    generator._generate_section_once = MagicMock(return_value=_make_section("good feedback"))
    generator.tone_checker.check = MagicMock(
        return_value=ToneCheckResult(is_constructive=True, raw_response="CONSTRUCTIVE")
    )

    result = generator.generate_section("skills_feedback", [], {})

    assert result.content == "good feedback"
    generator._generate_section_once.assert_called_once()


@patch("rag.generator.review_generator.openai.OpenAI")
def test_generate_section_regenerates_after_failed_tone_check(mock_openai: MagicMock) -> None:
    """A section that fails the tone check once should be regenerated and
    the regenerated (passing) version should be returned."""
    generator = ReviewGenerator(_make_config())
    generator._generate_section_once = MagicMock(
        side_effect=[_make_section("harsh feedback"), _make_section("better feedback")]
    )
    generator.tone_checker.check = MagicMock(
        side_effect=[
            ToneCheckResult(is_constructive=False, raw_response="NEGATIVE"),
            ToneCheckResult(is_constructive=True, raw_response="CONSTRUCTIVE"),
        ]
    )

    result = generator.generate_section("skills_feedback", [], {})

    assert result.content == "better feedback"
    assert generator._generate_section_once.call_count == 2


@patch("rag.generator.review_generator.openai.OpenAI")
def test_generate_section_falls_back_after_exhausting_retries(mock_openai: MagicMock) -> None:
    """If every attempt keeps failing the tone check, generate_section should
    stop retrying (not loop forever) and return the last attempt with a
    lowered confidence score, per PLAN.md's fallback-behavior edge case."""
    generator = ReviewGenerator(_make_config())
    generator._generate_section_once = MagicMock(return_value=_make_section("still harsh feedback"))
    generator.tone_checker.check = MagicMock(
        return_value=ToneCheckResult(is_constructive=False, raw_response="NEGATIVE")
    )

    result = generator.generate_section("skills_feedback", [], {})

    assert result.content == "still harsh feedback"
    assert result.confidence <= 0.3
    # 1 initial + MAX_TONE_RETRIES(2) regenerations = 3 total generation calls
    assert generator._generate_section_once.call_count == 3
