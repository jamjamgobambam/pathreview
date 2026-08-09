"""Tests for safety/tone_checker.py"""

from unittest.mock import MagicMock

import pytest

from safety.tone_checker import ToneChecker, ToneResult


@pytest.mark.unit
class TestToneCheckerHeuristic:
    """Tests for heuristic (no-LLM) mode of ToneChecker."""

    def setup_method(self) -> None:
        self.checker = ToneChecker(llm_client=None)

    def test_constructive_feedback_passes(self) -> None:
        """Specific, actionable feedback should be marked constructive."""
        feedback = (
            "Your README is missing a setup section. Consider adding installation "
            "instructions and a usage example to help contributors get started quickly."
        )
        result = self.checker.check("projects_feedback", feedback)

        assert result.is_constructive is True
        assert result.section_name == "projects_feedback"

    def test_dismissive_feedback_fails(self) -> None:
        """Feedback containing dismissive language should fail the check."""
        feedback = "This is terrible code and you will never be a good developer."
        result = self.checker.check("skills_feedback", feedback)

        assert result.is_constructive is False
        assert result.reason != ""

    def test_cannot_language_fails(self) -> None:
        """Feedback saying the developer can't do something should fail."""
        feedback = "You can't write clean code at this level."
        result = self.checker.check("skills_feedback", feedback)

        assert result.is_constructive is False

    def test_hopeless_language_fails(self) -> None:
        """Feedback with hopeless language should fail."""
        feedback = "Improving this project seems pointless at this stage."
        result = self.checker.check("projects_feedback", feedback)

        assert result.is_constructive is False

    def test_vague_short_feedback_fails(self) -> None:
        """Very short feedback with no actionable signal should fail."""
        feedback = "Needs work."
        result = self.checker.check("presentation_feedback", feedback)

        assert result.is_constructive is False

    def test_actionable_keyword_try_passes(self) -> None:
        """Feedback with 'try' should be flagged as actionable."""
        feedback = "Try adding type hints to your Python functions to improve readability."
        result = self.checker.check("skills_feedback", feedback)

        assert result.is_constructive is True

    def test_actionable_keyword_recommend_passes(self) -> None:
        """Feedback with 'recommend' should pass."""
        feedback = "I recommend exploring Docker to containerize your applications."
        result = self.checker.check("gaps_feedback", feedback)

        assert result.is_constructive is True

    def test_section_name_preserved_in_result(self) -> None:
        """ToneResult should carry the section name through."""
        feedback = "Consider adding unit tests to improve confidence in your code."
        result = self.checker.check("projects_feedback", feedback)

        assert result.section_name == "projects_feedback"

    def test_result_is_tone_result_instance(self) -> None:
        """check() should always return a ToneResult."""
        result = self.checker.check("skills_feedback", "some feedback")

        assert isinstance(result, ToneResult)

    def test_empty_feedback_fails(self) -> None:
        """Empty feedback string should fail as too vague."""
        result = self.checker.check("skills_feedback", "")

        assert result.is_constructive is False

    def test_case_insensitive_negative_pattern(self) -> None:
        """Negative pattern detection should be case-insensitive."""
        feedback = "This is TERRIBLE and shows you CANNOT improve."
        result = self.checker.check("skills_feedback", feedback)

        assert result.is_constructive is False


@pytest.mark.unit
class TestToneCheckerLLM:
    """Tests for LLM-backed mode using a mocked client."""

    def _make_mock_client(self, verdict: str, reason: str) -> MagicMock:
        """Build a mock OpenAI client returning the given verdict and reason."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = f"{verdict}\n{reason}"
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client

    def test_llm_constructive_verdict_passes(self) -> None:
        """LLM returning CONSTRUCTIVE should produce is_constructive=True."""
        client = self._make_mock_client(
            "CONSTRUCTIVE", "The feedback is specific and provides actionable steps."
        )
        checker = ToneChecker(llm_client=client)
        result = checker.check(
            "skills_feedback",
            "Consider learning TypeScript to strengthen your frontend skills.",
        )

        assert result.is_constructive is True
        assert "actionable" in result.reason

    def test_llm_negative_verdict_fails(self) -> None:
        """LLM returning NEGATIVE should produce is_constructive=False."""
        client = self._make_mock_client(
            "NEGATIVE", "The feedback is dismissive and offers no direction."
        )
        checker = ToneChecker(llm_client=client)
        result = checker.check("skills_feedback", "You are not good enough.")

        assert result.is_constructive is False
        assert result.reason != ""

    def test_llm_error_fails_open(self) -> None:
        """A transient LLM error should fail open (is_constructive=True)."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API timeout")
        checker = ToneChecker(llm_client=mock_client)
        result = checker.check("skills_feedback", "Some feedback text.")

        assert result.is_constructive is True
        assert "unavailable" in result.reason.lower()

    def test_llm_called_with_feedback_text(self) -> None:
        """The LLM client should be called with the feedback text in the prompt."""
        client = self._make_mock_client("CONSTRUCTIVE", "Good feedback.")
        checker = ToneChecker(llm_client=client)
        feedback = "Try refactoring your authentication module for clarity."
        checker.check("skills_feedback", feedback)

        call_args = client.chat.completions.create.call_args
        prompt_content = call_args.kwargs["messages"][0]["content"]
        assert feedback in prompt_content

    def test_llm_section_name_in_result(self) -> None:
        """Section name should be carried into the ToneResult."""
        client = self._make_mock_client("CONSTRUCTIVE", "Looks good.")
        checker = ToneChecker(llm_client=client)
        result = checker.check("presentation_feedback", "Great README structure.")

        assert result.section_name == "presentation_feedback"
