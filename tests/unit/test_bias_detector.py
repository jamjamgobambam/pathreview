"""Tests for bias_detector.py"""

import pytest

from safety.bias_detector import BiasDetector


@pytest.mark.unit
class TestBiasDetector:
    """Test suite for BiasDetector."""

    def test_dismissive_bootcamp_language_detected(self):
        """Test dismissive bootcamp language is detected as biased."""
        text = "bootcamp graduates can't write production code"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True
        assert reason != ""

    def test_bootcamp_lacks_rigor_detected(self):
        """Test 'bootcamp lacks rigor' language detected."""
        text = "bootcamp education lacks fundamentals"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_bootcamp_inadequate_training_detected(self):
        """Test 'bootcamp inadequate training' language detected."""
        text = "bootcamp training is inadequate for professional development"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_self_taught_comparison_detected(self):
        """Test self-taught vs traditional comparison detected."""
        text = "self-taught is never comparable to university education"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_positive_bootcamp_mention_not_flagged(self):
        """Test positive bootcamp mention is NOT flagged as biased."""
        text = "your bootcamp background shows strong fundamentals and problem-solving skills"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is False

    def test_neutral_bootcamp_mention_not_flagged(self):
        """Test neutral bootcamp mention is NOT flagged."""
        text = "this bootcamp project demonstrates good coding practices"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is False

    def test_educational_background_positive_not_flagged(self):
        """Test positive educational background mention not flagged."""
        text = "your bootcamp training has given you a solid foundation"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is False

    def test_demographic_assumption_age_detected(self):
        """Test demographic assumption about age detected."""
        text = "young developers can't handle complex systems"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True
        assert "demographic" in reason.lower()

    def test_demographic_assumption_old_detected(self):
        """Test age assumption about older developers detected."""
        text = "old aged programmer won't be able to learn new technologies"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_demographic_assumption_background_detected(self):
        """Test background assumption detected."""
        text = "person from poor background can't afford proper training"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_immigrant_developer_assumption_detected(self):
        """Test assumption about immigrant developers detected."""
        text = "immigrant developers can't communicate effectively in code reviews"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_international_developer_assumption_detected(self):
        """Test assumption about international developers detected."""
        text = "international developers struggle with American coding standards"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_clean_feedback_not_flagged(self):
        """Test clean, objective feedback is not flagged."""
        text = "You have demonstrated strong Python skills. Your code is well-organized and follows best practices."

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is False

    def test_technical_feedback_not_flagged(self):
        """Test pure technical feedback not flagged."""
        text = "Consider adding error handling to your API endpoints and documenting the parameters."

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is False

    def test_development_suggestion_not_flagged(self):
        """Test development suggestions not flagged."""
        text = "To improve your portfolio, try learning Kubernetes and contributing to open source."

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is False

    def test_case_insensitive_detection(self):
        """Test detection is case insensitive."""
        text = "BOOTCAMP GRADUATES LACK FUNDAMENTALS"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_return_value_structure(self):
        """Test return value has correct structure."""
        text = "some feedback"
        result = BiasDetector.detect_bias(text)

        assert isinstance(result, tuple)
        assert len(result) == 2
        is_biased, reason = result
        assert isinstance(is_biased, bool)
        assert isinstance(reason, str)

    def test_unbiased_returns_empty_reason(self):
        """Test unbiased feedback returns empty reason string."""
        text = "Great coding skills"

        is_biased, reason = BiasDetector.detect_bias(text)

        if is_biased is False:
            assert reason == ""

    def test_biased_returns_reason(self):
        """Test biased feedback returns non-empty reason."""
        text = "bootcamp graduates can't code"

        is_biased, reason = BiasDetector.detect_bias(text)

        if is_biased is True:
            assert reason != ""
            assert len(reason) > 0

    def test_empty_text(self):
        """Test with empty text."""
        is_biased, reason = BiasDetector.detect_bias("")

        assert is_biased is False

    def test_whitespace_only(self):
        """Test with whitespace only."""
        is_biased, reason = BiasDetector.detect_bias("   \n\t  ")

        assert is_biased is False

    def test_coding_bootcamp_variant(self):
        """Test 'coding bootcamp' variant is detected."""
        text = "coding bootcamp graduates can't write enterprise code"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_online_course_bias_detected(self):
        """Test online course dismissal detected."""
        text = "online course education is insufficient for real work"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_developer_vs_programmer_distinction(self):
        """Test both developer and programmer terms detected."""
        text_dev = "bootcamp developers can't handle production systems"
        text_prog = "bootcamp programmers lack proper training"

        is_biased_dev, _ = BiasDetector.detect_bias(text_dev)
        is_biased_prog, _ = BiasDetector.detect_bias(text_prog)

        assert is_biased_dev is True
        assert is_biased_prog is True

    def test_multiple_bias_indicators(self):
        """Test text with multiple bias indicators."""
        text = "young bootcamp graduates can't write code and immigrant developers lack fundamentals"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_negative_educational_claim(self):
        """Test negative claims about education detected."""
        text = "self-taught developers are not equal to university graduates"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_working_class_assumption(self):
        """Test working-class assumption detected."""
        text = "person from working class background won't succeed in tech"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_rich_poor_assumption(self):
        """Test rich/poor background assumption detected."""
        text = "developers from poor backgrounds can't afford proper tools"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_foreign_developer_struggle_assumption(self):
        """Test assumption about foreign developers struggling."""
        text = "foreign developers struggle with English-first codebases"

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is True

    def test_skill_assessment_not_biased(self):
        """Test skill assessment without bias language."""
        text = "Your JavaScript skills are at an intermediate level. Practice would help advance to senior level."

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is False

    def test_comparative_without_bias(self):
        """Test comparison without biased assumptions."""
        text = "Your bootcamp education covers practical skills. University education provides theory. Both have value."

        is_biased, reason = BiasDetector.detect_bias(text)

        assert is_biased is False

    def test_assumption_vs_observation(self):
        """Test that observations are not flagged, assumptions are."""
        observation = "your resume shows bootcamp attendance"  # Factual
        assumption = "bootcamp attendance means inadequate training"  # Biased

        is_biased_obs, _ = BiasDetector.detect_bias(observation)
        is_biased_ass, _ = BiasDetector.detect_bias(assumption)

        assert is_biased_obs is False  # Factual
        assert is_biased_ass is True  # Biased assumption
