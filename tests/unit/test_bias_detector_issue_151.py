"""Regression tests for Issue #151 bias detector phrasing."""

import pytest

from safety.bias_detector import BiasDetector


@pytest.mark.unit
class TestBiasDetectorIssue151:
    """Test natural-language variations described in Issue #151."""

    def test_long_bootcamp_dismissal_detected(self) -> None:
        """Detect longer dismissive bootcamp phrasing."""
        text = (
            "The candidate only attended a bootcamp, so this project "
            "lacks the rigor of a formal CS education"
        )

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True
        assert reason == "Dismissive language about educational background"

    def test_age_context_assumption_detected(self) -> None:
        """Detect an age assumption expressed through context."""
        text = "Given their age, they likely cannot keep up " "with modern frameworks"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True
        assert reason == "Demographic assumptions detected"

    def test_neutral_bootcamp_statement_not_detected(self) -> None:
        """Keep neutral bootcamp statements unflagged."""
        text = (
            "The candidate attended a bootcamp and demonstrated " "strong programming fundamentals"
        )

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is False
        assert reason == ""
