"""Tests for content_filter.py."""

import pytest

from safety.content_filter import ContentFilter


@pytest.mark.unit
class TestContentFilterToneCheck:
    """Reproduction test for issue #69.

    ContentFilter.filter() only matches specific harmful regex patterns
    (self-harm, hate speech, illegal activity) — it has no concept of
    constructive vs. discouraging tone. The text below is clearly
    dismissive/discouraging feedback, but nothing flags it today. This
    test should start passing once issue #69 adds tone classification.
    """

    def test_discouraging_feedback_is_flagged(self) -> None:
        text = (
            "Your code is sloppy and it's obvious you didn't try very hard "
            "on this. Frankly, this project isn't worth including in a "
            "portfolio at all — it's amateur work and reflects poorly on "
            "you as a candidate."
        )

        _, was_flagged = ContentFilter.filter(text)

        assert was_flagged is True
