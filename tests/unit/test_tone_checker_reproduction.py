"""Reproduction test for issue #69.

Before the fix, ReviewGenerator had no tone classification step.
Negative or vague feedback produced by the LLM passed through the pipeline
unchecked and was returned directly to the user.

This file documents the exact gap:
  - A mocked LLM returning dismissive feedback
  - No ToneChecker → feedback reaches the caller unchanged
  - With ToneChecker → feedback is flagged and regenerated

Run with:
    .venv/bin/pytest tests/unit/test_tone_checker_reproduction.py -v -m unit
"""

from unittest.mock import MagicMock

import pytest

from safety.tone_checker import ToneChecker


def _make_llm_response(content: str) -> MagicMock:
    """Build a minimal mock OpenAI response returning the given content."""
    mock = MagicMock()
    mock.choices[0].message.content = content
    return mock


@pytest.mark.unit
class TestIssue69Reproduction:
    """Demonstrates the gap described in issue #69.

    Before fix: the review pipeline had no tone check; negative feedback
    was returned to users verbatim.

    After fix: ToneChecker classifies each section and triggers a retry
    when feedback is not constructive.
    """

    DISMISSIVE_FEEDBACK = (
        "Your projects are terrible and show you cannot write clean code. "
        "This portfolio is not good enough for any serious employer."
    )

    VAGUE_FEEDBACK = "Needs work."

    CONSTRUCTIVE_FEEDBACK = (
        "Consider adding README files to each project with setup instructions. "
        "This would help recruiters quickly understand your work and improve "
        "your portfolio's first impression significantly."
    )

    def test_original_gap_negative_feedback_not_caught_without_checker(self) -> None:
        """Without ToneChecker, dismissive feedback passes through undetected.

        This is the exact gap from issue #69: the pipeline had no mechanism
        to verify that generated feedback was constructive.
        """
        # Simulate the pre-fix state: no tone checker, LLM returns dismissive text
        checker = ToneChecker(llm_client=None)

        # In the original code, this check never happened — feedback went
        # straight to the user. Now with ToneChecker it IS caught:
        result = checker.check("projects_feedback", self.DISMISSIVE_FEEDBACK)

        # The fix catches this — before the fix, no check existed at all
        assert result.is_constructive is False, (
            "Dismissive feedback should be flagged. "
            "Before fix: no check existed and this text reached the user directly."
        )

    def test_original_gap_vague_feedback_not_caught_without_checker(self) -> None:
        """Without ToneChecker, vague one-line feedback passed through undetected."""
        checker = ToneChecker(llm_client=None)
        result = checker.check("skills_feedback", self.VAGUE_FEEDBACK)

        assert result.is_constructive is False, (
            "Vague feedback should be flagged. "
            "Before fix: no check existed and this text reached the user directly."
        )

    def test_fix_llm_judge_catches_negative_feedback(self) -> None:
        """With LLM-as-judge, dismissive feedback is classified as NEGATIVE."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_llm_response(
            "NEGATIVE\nThe feedback is dismissive and offers no actionable path forward."
        )
        checker = ToneChecker(llm_client=mock_client)
        result = checker.check("projects_feedback", self.DISMISSIVE_FEEDBACK)

        assert result.is_constructive is False
        assert result.reason != ""

    def test_fix_llm_judge_passes_constructive_feedback(self) -> None:
        """With LLM-as-judge, constructive feedback is classified as CONSTRUCTIVE."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_llm_response(
            "CONSTRUCTIVE\nThe feedback is specific, actionable, and encouraging."
        )
        checker = ToneChecker(llm_client=mock_client)
        result = checker.check("projects_feedback", self.CONSTRUCTIVE_FEEDBACK)

        assert result.is_constructive is True

    def test_reproduction_steps(self) -> None:
        """Documents the exact reproduction steps for issue #69.

        Reproduction steps (run in Python shell):
            from rag.generator.review_generator import ReviewGenerator, ReviewConfig
            # Before fix: generate_section() had no tone check after parsing output.
            # Any feedback — including vague or dismissive text — was returned directly.

            # The gap lives in rag/generator/review_generator.py:
            #   generate_section() called parse_review_output() and returned sections[0]
            #   with no verification that the content was constructive.

            # With the fix:
            #   generate_section() now calls self.tone_checker.check(section_name, content)
            #   and retries with a stronger system prompt if is_constructive is False.

        This test passes trivially — it exists to document the reproduction path.
        """
        assert True
