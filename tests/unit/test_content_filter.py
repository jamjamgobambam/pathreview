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

    def test_discouraging_text_is_not_redacted_in_place(self) -> None:
        """Discouraging tone is flagged, not rewritten — regeneration handles it."""
        text = "Your code is sloppy and amateur work."

        filtered_text, was_flagged = ContentFilter.filter(text)

        assert was_flagged is True
        assert filtered_text == text

    def test_give_up_language_is_flagged(self) -> None:
        text = "Honestly, you should just give up on programming."

        _, was_flagged = ContentFilter.filter(text)

        assert was_flagged is True

    def test_waste_of_time_language_is_flagged(self) -> None:
        text = "This whole project was a waste of time."

        _, was_flagged = ContentFilter.filter(text)

        assert was_flagged is True

    def test_case_insensitive_discouraging_detection(self) -> None:
        text = "THIS PROJECT IS AMATEUR WORK."

        _, was_flagged = ContentFilter.filter(text)

        assert was_flagged is True

    def test_constructive_feedback_is_not_flagged(self) -> None:
        text = (
            "Your API design shows solid understanding of REST principles. "
            "Consider adding input validation and a few more unit tests "
            "around the edge cases to make this even stronger."
        )

        _, was_flagged = ContentFilter.filter(text)

        assert was_flagged is False

    def test_harsh_but_factual_feedback_is_not_flagged(self) -> None:
        """Blunt, critical feedback about the work itself isn't discouraging tone."""
        text = (
            "This function has three unhandled exceptions and no test "
            "coverage. It will fail in production under common edge cases."
        )

        _, was_flagged = ContentFilter.filter(text)

        assert was_flagged is False

    def test_empty_text_is_not_flagged(self) -> None:
        filtered_text, was_flagged = ContentFilter.filter("")

        assert was_flagged is False
        assert filtered_text == ""

    def test_harmful_content_still_redacted(self) -> None:
        """Existing harmful-content redaction behavior is unaffected."""
        text = "You should just hurt yourself over this."

        filtered_text, was_flagged = ContentFilter.filter(text)

        assert was_flagged is True
        assert "[CONTENT REMOVED]" in filtered_text
