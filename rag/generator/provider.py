"""Factory for selecting a review generator implementation."""

from typing import Protocol, runtime_checkable

from core.config import settings

from .mock_generator import MockReviewGenerator
from .output_parser import FeedbackSection

# OpenAI exposes no model name through Settings (only the OpenRouter model is
# configurable), so the OpenAI branch needs a default of its own.
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"


@runtime_checkable
class ReviewGeneratorProtocol(Protocol):
    """The generation surface every provider must offer.

    Both :class:`~rag.generator.review_generator.ReviewGenerator` and
    :class:`~rag.generator.mock_generator.MockReviewGenerator` satisfy this
    structurally, so callers can hold either without importing ``openai``.
    """

    def generate_section(
        self,
        section_name: str,
        context_chunks: list[dict],
        profile_data: dict,
    ) -> FeedbackSection:
        """Generate feedback for a single section."""
        ...

    def generate_full_review(
        self,
        profile_data: dict,
        retrieved_chunks: list[dict],
    ) -> list[FeedbackSection]:
        """Generate feedback for every review section."""
        ...


def get_review_generator(provider_name: str) -> ReviewGeneratorProtocol:
    """Get a review generator by provider name.

    Mirrors :func:`ingestion.embeddings.provider.get_embedding_provider` so that
    a single ``LLM_PROVIDER`` value selects both the embedding and the generation
    implementation. The ``"mock"`` branch constructs no HTTP client and imports
    no networking library, which is what keeps ``LLM_PROVIDER=mock`` runs fully
    offline.

    Args:
        provider_name: One of "mock", "openai", "openrouter"

    Returns:
        A generator implementing ReviewGeneratorProtocol

    Raises:
        ValueError: If provider_name is unknown, or a live provider is selected
            without the API key it needs
    """
    provider_name_lower = provider_name.lower().strip()

    if provider_name_lower == "mock":
        return MockReviewGenerator()

    if provider_name_lower == "openai":
        return _build_live_generator(
            api_key=settings.openai_api_key,
            base_url=OPENAI_BASE_URL,
            model=OPENAI_DEFAULT_MODEL,
            key_setting="OPENAI_API_KEY",
        )

    if provider_name_lower == "openrouter":
        return _build_live_generator(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            key_setting="OPENROUTER_API_KEY",
        )

    raise ValueError(
        f"Unknown review generator provider: {provider_name}. "
        "Supported: 'mock', 'openai', 'openrouter'"
    )


def _build_live_generator(
    api_key: str,
    base_url: str,
    model: str,
    key_setting: str,
) -> ReviewGeneratorProtocol:
    """Construct the networked generator, refusing to start without credentials.

    ``ReviewGenerator.__init__`` builds an ``openai.OpenAI`` client eagerly and
    raises ``OpenAIError`` when credentials are missing. Checking the key first
    turns that into an actionable error before any benchmark work begins, rather
    than a client-library failure part-way through a run.

    Args:
        api_key: Credential for the provider
        base_url: Provider API base URL
        model: Model identifier to request
        key_setting: Environment variable name quoted in the error message

    Returns:
        A configured ReviewGenerator

    Raises:
        ValueError: If api_key is empty
    """
    if not api_key:
        raise ValueError(
            f"{key_setting} is not set. Set it, or use LLM_PROVIDER=mock for offline runs."
        )

    # Imported lazily so that selecting the mock provider never imports openai.
    from .review_generator import ReviewConfig, ReviewGenerator

    return ReviewGenerator(ReviewConfig(api_key=api_key, base_url=base_url, model=model))
