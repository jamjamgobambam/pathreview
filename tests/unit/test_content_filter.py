"""Tests for content_filter.py, including reproduction of issue #69."""

from safety.content_filter import ContentFilter


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
