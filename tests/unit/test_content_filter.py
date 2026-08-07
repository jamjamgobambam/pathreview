"""Tests for content_filter.py — ContentFilter and ToneClassifier (issue #69)."""

from unittest.mock import Mock

import pytest

from safety.content_filter import ContentFilter, ToneClassifier


def _mock_client(content: str) -> Mock:
    """Build a mock OpenAI-compatible client returning a fixed message content."""
    client = Mock()
    message = Mock()
    message.content = content
    choice = Mock()
    choice.message = message
    response = Mock()
    response.choices = [choice]
    client.chat.completions.create.return_value = response
    return client


@pytest.mark.unit
class TestContentFilter:
    """Existing harmful-content filtering behavior."""

    def test_clean_text_passes_through(self):
        text = "Your projects show strong Python skills."
        filtered, was_filtered = ContentFilter.filter(text)
        assert was_filtered is False
        assert filtered == text

    def test_harmful_phrase_is_redacted(self):
        text = "You are a worthless person and should give up."
        filtered, was_filtered = ContentFilter.filter(text)
        assert was_filtered is True
        assert "[CONTENT REMOVED]" in filtered


@pytest.mark.unit
class TestToneClassifier:
    """Tone classification for constructive vs non-constructive feedback."""

    def test_constructive_feedback_passes(self):
        client = _mock_client('{"constructive": true, "reason": "actionable and specific"}')
        classifier = ToneClassifier(client, model="test-model")

        is_constructive, reason = classifier.classify(
            "Add a README with setup steps to make your projects easier to run."
        )

        assert is_constructive is True
        assert reason == "actionable and specific"

    def test_negative_feedback_is_flagged(self):
        client = _mock_client('{"constructive": false, "reason": "dismissive and vague"}')
        classifier = ToneClassifier(client, model="test-model")

        is_constructive, reason = classifier.classify("This portfolio is bad. Start over.")

        assert is_constructive is False
        assert reason == "dismissive and vague"

    def test_verdict_extracted_from_surrounding_prose(self):
        # LLM sometimes wraps JSON in extra text; parser should still find it.
        client = _mock_client(
            'Here is my verdict:\n{"constructive": false, "reason": "too harsh"}\nThanks.'
        )
        classifier = ToneClassifier(client, model="test-model")

        is_constructive, _ = classifier.classify("harsh feedback")

        assert is_constructive is False

    def test_empty_text_fails_open(self):
        client = _mock_client('{"constructive": false, "reason": "unused"}')
        classifier = ToneClassifier(client, model="test-model")

        is_constructive, _ = classifier.classify("   ")

        # Empty input should not even call the LLM; it defaults to constructive.
        assert is_constructive is True
        client.chat.completions.create.assert_not_called()

    def test_unparseable_response_fails_open(self):
        client = _mock_client("I could not produce JSON, sorry.")
        classifier = ToneClassifier(client, model="test-model")

        is_constructive, _ = classifier.classify("some feedback")

        assert is_constructive is True

    def test_llm_error_fails_open(self):
        client = Mock()
        client.chat.completions.create.side_effect = RuntimeError("api down")
        classifier = ToneClassifier(client, model="test-model")

        is_constructive, reason = classifier.classify("some feedback")

        assert is_constructive is True
        assert "unavailable" in reason
