"""Tests for review_generator.py"""

from unittest.mock import Mock

import pytest

from rag.generator.review_generator import ReviewConfig, ReviewGenerator


def _mock_llm_response(content: str) -> Mock:
    """Build a Mock shaped like an OpenAI chat completion response."""
    response = Mock()
    response.choices = [Mock(message=Mock(content=content))]
    return response


@pytest.mark.unit
class TestReviewGeneratorToneCheck:
    """Test suite for ReviewGenerator's tone-check regenerate-on-fail behavior."""

    @pytest.fixture
    def generator(self) -> ReviewGenerator:
        """Create a ReviewGenerator with a dummy config (no real API calls)."""
        config = ReviewConfig(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="test-model",
        )
        return ReviewGenerator(config)

    @pytest.fixture
    def profile_data(self) -> dict:
        return {"github_username": "octocat", "projects": []}

    def test_constructive_first_attempt_is_returned_unchanged(
        self, generator: ReviewGenerator, profile_data: dict
    ) -> None:
        """A constructive section on the first try isn't regenerated."""
        constructive_text = (
            "Your API design shows solid understanding of REST principles. "
            "Consider adding input validation and more tests around edge cases."
        )
        generator.client.chat.completions.create = Mock(
            return_value=_mock_llm_response(constructive_text)
        )

        section = generator.generate_section("skills_feedback", [], profile_data)

        assert section.content == constructive_text
        assert generator.client.chat.completions.create.call_count == 1

    def test_discouraging_feedback_triggers_one_regeneration(
        self, generator: ReviewGenerator, profile_data: dict
    ) -> None:
        """A discouraging first attempt is discarded in favor of a constructive retry."""
        discouraging_text = (
            "Your code is sloppy and it's obvious you didn't try very hard "
            "on this. This project isn't worth including in a portfolio at "
            "all — it's amateur work and reflects poorly on you."
        )
        constructive_text = (
            "Consider adding docstrings to your public functions and "
            "expanding test coverage around the parsing edge cases."
        )
        generator.client.chat.completions.create = Mock(
            side_effect=[
                _mock_llm_response(discouraging_text),
                _mock_llm_response(constructive_text),
            ]
        )

        section = generator.generate_section("skills_feedback", [], profile_data)

        assert section.content == constructive_text
        assert generator.client.chat.completions.create.call_count == 2

    def test_vague_feedback_triggers_regeneration(
        self, generator: ReviewGenerator, profile_data: dict
    ) -> None:
        """Vague, non-actionable feedback is regenerated even without discouraging language."""
        vague_text = "Great work!"
        constructive_text = (
            "Add error handling around the database calls and document the "
            "expected exceptions in the function docstrings."
        )
        generator.client.chat.completions.create = Mock(
            side_effect=[
                _mock_llm_response(vague_text),
                _mock_llm_response(constructive_text),
            ]
        )

        section = generator.generate_section("skills_feedback", [], profile_data)

        assert section.content == constructive_text
        assert generator.client.chat.completions.create.call_count == 2

    def test_exhausted_retries_returns_safe_fallback(
        self, generator: ReviewGenerator, profile_data: dict
    ) -> None:
        """If every attempt fails the tone check, return a safe fallback instead of looping."""
        discouraging_text = "This is amateur work and isn't worth including."
        generator.client.chat.completions.create = Mock(
            return_value=_mock_llm_response(discouraging_text)
        )

        section = generator.generate_section("skills_feedback", [], profile_data)

        # 1 initial attempt + MAX_TONE_REGENERATION_ATTEMPTS retries
        expected_calls = 1 + ReviewGenerator.MAX_TONE_REGENERATION_ATTEMPTS
        assert generator.client.chat.completions.create.call_count == expected_calls
        assert section.content != discouraging_text
        assert section.confidence == 0.0
        assert section.section_name == "skills_feedback"

    def test_regeneration_is_bounded_not_infinite(
        self, generator: ReviewGenerator, profile_data: dict
    ) -> None:
        """Regeneration never exceeds the configured max, even if every attempt fails."""
        generator.client.chat.completions.create = Mock(return_value=_mock_llm_response("Fine."))

        generator.generate_section("skills_feedback", [], profile_data)

        assert generator.client.chat.completions.create.call_count <= (
            1 + ReviewGenerator.MAX_TONE_REGENERATION_ATTEMPTS
        )
