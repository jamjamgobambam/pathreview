"""Tests for the tone-check regenerate loop in ReviewGenerator (issue #69)."""

from unittest.mock import Mock

import pytest

from rag.generator.review_generator import ReviewConfig, ReviewGenerator


def _make_response(content: str) -> Mock:
    """Build a mock chat-completion response wrapping ``content``."""
    message = Mock()
    message.content = content
    choice = Mock()
    choice.message = message
    response = Mock()
    response.choices = [choice]
    return response


def _make_generator(**config_overrides) -> ReviewGenerator:
    """Construct a ReviewGenerator with a dummy config (no network calls)."""
    config = ReviewConfig(
        api_key="test-key",
        base_url="https://example.invalid/v1",
        model="test-model",
        **config_overrides,
    )
    return ReviewGenerator(config)


PROFILE = {"github_username": "octocat", "projects": [{"name": "p1"}]}
CHUNKS = [{"text": "some context", "metadata": {"source_id": "s1"}, "score": 0.9}]


@pytest.mark.unit
class TestToneRegenerationLoop:
    """generate_section should regenerate non-constructive sections."""

    def test_constructive_first_try_no_regeneration(self):
        gen = _make_generator()
        gen.client = Mock()
        gen.client.chat.completions.create.return_value = _make_response(
            "Great, actionable feedback."
        )
        gen.tone_classifier = Mock()
        gen.tone_classifier.classify.return_value = (True, "constructive")

        section = gen.generate_section("first_impression", CHUNKS, PROFILE)

        assert section.content == "Great, actionable feedback."
        # Only one generation call — no regeneration needed.
        assert gen.client.chat.completions.create.call_count == 1

    def test_negative_then_constructive_triggers_one_regeneration(self):
        gen = _make_generator(max_tone_retries=2)
        gen.client = Mock()
        gen.client.chat.completions.create.side_effect = [
            _make_response("This is dismissive junk."),
            _make_response("Here is a specific, encouraging rewrite."),
        ]
        gen.tone_classifier = Mock()
        gen.tone_classifier.classify.side_effect = [
            (False, "dismissive"),
            (True, "now constructive"),
        ]

        section = gen.generate_section("first_impression", CHUNKS, PROFILE)

        assert section.content == "Here is a specific, encouraging rewrite."
        # Original attempt + one regeneration.
        assert gen.client.chat.completions.create.call_count == 2

    def test_retries_exhausted_returns_best_effort(self):
        gen = _make_generator(max_tone_retries=2)
        gen.client = Mock()
        gen.client.chat.completions.create.side_effect = [
            _make_response("draft one"),
            _make_response("draft two"),
            _make_response("draft three"),
        ]
        gen.tone_classifier = Mock()
        # Never constructive.
        gen.tone_classifier.classify.return_value = (False, "still bad")

        section = gen.generate_section("first_impression", CHUNKS, PROFILE)

        # 1 original + 2 retries = 3 generation calls; last draft delivered.
        assert gen.client.chat.completions.create.call_count == 3
        assert section.content == "draft three"

    def test_tone_check_disabled_skips_classifier(self):
        gen = _make_generator(tone_check_enabled=False)
        gen.client = Mock()
        gen.client.chat.completions.create.return_value = _make_response("whatever tone")

        assert gen.tone_classifier is None

        section = gen.generate_section("first_impression", CHUNKS, PROFILE)

        assert section.content == "whatever tone"
        assert gen.client.chat.completions.create.call_count == 1
