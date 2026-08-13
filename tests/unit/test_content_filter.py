"""Tests for content_filter.py, including reproduction of issue #69."""

from unittest.mock import MagicMock

from safety.content_filter import ContentFilter, ToneChecker


def test_harsh_feedback_not_caught_by_tone_check() -> None:
    """Reproduces issue #69: no tone check exists for constructive feedback.

    ContentFilter only catches explicitly harmful patterns (self-harm,
    slurs, illegal activity, etc). It has no concept of discouraging or
    unconstructive tone, so harsh-but-not-"harmful" feedback passes
    through unfiltered. This test demonstrates that gap.
    """
    harsh_content = "This work is mediocre and shows little effort or skill."
    filtered_text, was_filtered = ContentFilter.filter(harsh_content)

    # Currently passes unchanged because ContentFilter has no tone check
    assert filtered_text == harsh_content
    assert was_filtered is False


def _mock_client(verdict: str) -> MagicMock:
    """Build a mock OpenAI-compatible client that returns a fixed verdict."""
    client = MagicMock()
    client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content=verdict))
    ]
    return client


def test_tone_checker_accepts_constructive_feedback() -> None:
    client = _mock_client("CONSTRUCTIVE")
    checker = ToneChecker(client, model="test-model")

    result = checker.check(
        "Consider adding unit tests to your API routes - this would "
        "strengthen your project and show attention to reliability."
    )

    assert result.is_constructive is True


def test_tone_checker_rejects_negative_feedback() -> None:
    client = _mock_client("NEGATIVE")
    checker = ToneChecker(client, model="test-model")

    result = checker.check("This work is mediocre and shows little effort or skill.")

    assert result.is_constructive is False


def test_tone_checker_accepts_critical_but_actionable_feedback() -> None:
    """Feedback with real criticism should still pass if it's actionable."""
    client = _mock_client("CONSTRUCTIVE")
    checker = ToneChecker(client, model="test-model")

    result = checker.check(
        "Your README is missing setup instructions, which makes it hard for "
        "reviewers to run your project. Adding a quickstart section would fix this."
    )

    assert result.is_constructive is True


def test_tone_checker_handles_empty_content() -> None:
    """Empty/short feedback has nothing to classify, so it shouldn't be rejected."""
    client = _mock_client("NEGATIVE")
    checker = ToneChecker(client, model="test-model")

    result = checker.check("")

    assert result.is_constructive is True
