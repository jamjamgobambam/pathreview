"""Tests for rag/generator/provider.py"""

from unittest.mock import patch

import pytest

from core.config import Settings, settings
from rag.generator.mock_generator import MockReviewGenerator
from rag.generator.provider import (
    OPENAI_BASE_URL,
    OPENAI_DEFAULT_MODEL,
    ReviewGeneratorProtocol,
    get_review_generator,
)
from rag.generator.review_generator import ReviewGenerator


@pytest.mark.unit
class TestGetReviewGenerator:
    """Test suite for the review generator factory."""

    def test_mock_provider_returns_mock_generator(self):
        """Test 'mock' resolves to the deterministic offline generator."""
        generator = get_review_generator("mock")

        assert isinstance(generator, MockReviewGenerator)

    def test_mock_provider_is_case_and_whitespace_insensitive(self):
        """Test provider names are normalised like get_embedding_provider does."""
        assert isinstance(get_review_generator("  MOCK  "), MockReviewGenerator)

    def test_unknown_provider_raises_value_error(self):
        """Test an unrecognised provider name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown review generator provider"):
            get_review_generator("anthropic")

    def test_empty_provider_raises_value_error(self):
        """Test an empty provider name raises ValueError."""
        with pytest.raises(ValueError):
            get_review_generator("")

    def test_mock_provider_constructs_no_openai_client(self):
        """Test selecting the mock provider never builds a live model client."""
        with patch("openai.OpenAI") as mock_client:
            get_review_generator("mock")

        mock_client.assert_not_called()

    def test_openai_provider_without_key_raises_before_client_construction(self):
        """Test a missing OpenAI key fails with an actionable error, not OpenAIError."""
        with (
            patch.object(settings, "openai_api_key", ""),
            patch("openai.OpenAI") as mock_client,
            pytest.raises(ValueError, match="OPENAI_API_KEY"),
        ):
            get_review_generator("openai")

        mock_client.assert_not_called()

    def test_openrouter_provider_without_key_raises_before_client_construction(self):
        """Test a missing OpenRouter key fails with an actionable error."""
        with (
            patch.object(settings, "openrouter_api_key", ""),
            patch("openai.OpenAI") as mock_client,
            pytest.raises(ValueError, match="OPENROUTER_API_KEY"),
        ):
            get_review_generator("openrouter")

        mock_client.assert_not_called()

    def test_openai_provider_with_key_builds_live_generator(self):
        """Test the OpenAI branch configures the live generator from settings."""
        with patch.object(settings, "openai_api_key", "test-key"), patch("openai.OpenAI"):
            generator = get_review_generator("openai")

        assert isinstance(generator, ReviewGenerator)
        assert generator.config.api_key == "test-key"
        assert generator.config.base_url == OPENAI_BASE_URL
        assert generator.config.model == OPENAI_DEFAULT_MODEL

    def test_openrouter_provider_with_key_builds_live_generator(self):
        """Test the OpenRouter branch configures the live generator from settings."""
        with patch.object(settings, "openrouter_api_key", "test-key"), patch("openai.OpenAI"):
            generator = get_review_generator("openrouter")

        assert isinstance(generator, ReviewGenerator)
        assert generator.config.api_key == "test-key"
        assert generator.config.base_url == settings.openrouter_base_url
        assert generator.config.model == settings.openrouter_model

    def test_mock_generator_satisfies_protocol(self):
        """Test the mock generator implements the shared generation surface."""
        assert isinstance(get_review_generator("mock"), ReviewGeneratorProtocol)

    def test_live_generator_satisfies_protocol(self):
        """Test the live generator implements the same surface as the mock."""
        with patch.object(settings, "openai_api_key", "test-key"), patch("openai.OpenAI"):
            generator = get_review_generator("openai")

        assert isinstance(generator, ReviewGeneratorProtocol)

    def test_default_settings_provider_is_offline(self):
        """Test the shipped LLM_PROVIDER default resolves to an offline generator."""
        default_provider = Settings.model_fields["llm_provider"].default

        assert isinstance(get_review_generator(default_provider), MockReviewGenerator)
