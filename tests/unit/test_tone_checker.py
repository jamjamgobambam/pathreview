"""Tests for tone_checker.py"""

import pytest

from safety.tone_checker import ToneChecker


@pytest.mark.unit
class TestToneChecker:
    """Test suite for ToneChecker."""

    def test_discouraging_feedback_is_not_constructive(self) -> None:
        """Test discouraging feedback is classified as not constructive."""
        text = (
            "Your code is sloppy and it's obvious you didn't try very hard "
            "on this. Frankly, this project isn't worth including in a "
            "portfolio at all — it's amateur work and reflects poorly on "
            "you as a candidate."
        )

        is_constructive, reason = ToneChecker.check_tone(text)

        assert is_constructive is False
        assert reason != ""

    def test_constructive_feedback_is_flagged_constructive(self) -> None:
        """Test specific, actionable feedback is classified as constructive."""
        text = (
            "Your API design shows solid understanding of REST principles. "
            "Consider adding input validation and a few more unit tests "
            "around the edge cases to make this even stronger."
        )

        is_constructive, reason = ToneChecker.check_tone(text)

        assert is_constructive is True
        assert reason == ""

    def test_harsh_but_factual_feedback_is_constructive(self) -> None:
        """Blunt, critical feedback about the work itself isn't discouraging tone."""
        text = (
            "This function has three unhandled exceptions and no test "
            "coverage. It will fail in production under common edge cases."
        )

        is_constructive, reason = ToneChecker.check_tone(text)

        assert is_constructive is True

    def test_empty_feedback_is_not_constructive(self) -> None:
        """Test empty feedback is not constructive."""
        is_constructive, reason = ToneChecker.check_tone("")

        assert is_constructive is False
        assert reason != ""

    def test_whitespace_only_feedback_is_not_constructive(self) -> None:
        """Test whitespace-only feedback is not constructive."""
        is_constructive, reason = ToneChecker.check_tone("   \n\t  ")

        assert is_constructive is False

    def test_very_short_feedback_is_not_constructive(self) -> None:
        """Test near-empty feedback is not actionable."""
        is_constructive, reason = ToneChecker.check_tone("Fine.")

        assert is_constructive is False
        assert reason != ""

    def test_vague_generic_praise_is_not_constructive(self) -> None:
        """Test generic praise with no specifics is not actionable."""
        is_constructive, reason = ToneChecker.check_tone("Great work!")

        assert is_constructive is False

    def test_vague_looks_good_is_not_constructive(self) -> None:
        """Test 'looks good' alone is not actionable."""
        is_constructive, reason = ToneChecker.check_tone("Looks good.")

        assert is_constructive is False

    def test_give_up_language_is_not_constructive(self) -> None:
        """Test feedback telling the user to give up is not constructive."""
        text = "Honestly, you should just give up on programming."

        is_constructive, reason = ToneChecker.check_tone(text)

        assert is_constructive is False

    def test_return_value_structure(self) -> None:
        """Test return value has correct structure."""
        result = ToneChecker.check_tone("Some feedback that is long enough to pass.")

        assert isinstance(result, tuple)
        assert len(result) == 2
        is_constructive, reason = result
        assert isinstance(is_constructive, bool)
        assert isinstance(reason, str)

    def test_constructive_returns_empty_reason(self) -> None:
        """Test constructive feedback returns empty reason string."""
        text = "Consider refactoring this into smaller, testable functions."

        is_constructive, reason = ToneChecker.check_tone(text)

        if is_constructive is True:
            assert reason == ""

    def test_not_constructive_returns_reason(self) -> None:
        """Test non-constructive feedback returns non-empty reason."""
        is_constructive, reason = ToneChecker.check_tone("")

        if is_constructive is False:
            assert reason != ""
            assert len(reason) > 0

    def test_case_insensitive_discouraging_detection(self) -> None:
        """Test discouraging detection works regardless of case."""
        text = "THIS PROJECT IS AMATEUR WORK AND ISN'T WORTH INCLUDING."

        is_constructive, reason = ToneChecker.check_tone(text)

        assert is_constructive is False

    def test_specific_suggestions_are_constructive(self) -> None:
        """Test feedback with concrete, specific suggestions passes."""
        text = (
            "Add error handling around the database calls in profile_service.py "
            "and document the expected exceptions in the function docstrings."
        )

        is_constructive, reason = ToneChecker.check_tone(text)

        assert is_constructive is True
