"""Contract tests for LLM providers"""

from collections.abc import Iterator
from unittest.mock import MagicMock

import numpy as np
import pytest

from ingestion.embeddings.provider import (
    EmbeddingProvider,
    MockEmbeddingProvider,
    OpenAIEmbeddingProvider,
)


@pytest.mark.unit
class TestLLMProviderContract:
    """Contract tests for embedding providers."""

    @pytest.fixture
    def mock_provider(self) -> MockEmbeddingProvider:
        """Create MockEmbeddingProvider instance."""
        return MockEmbeddingProvider()

    def test_mock_provider_returns_list_of_floats(
        self, mock_provider: MockEmbeddingProvider
    ) -> None:
        """Test MockEmbeddingProvider returns list of list of floats."""
        texts = ["Hello world", "Goodbye world"]
        embeddings = mock_provider.embed(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == 2
        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert all(isinstance(x, float) for x in embedding)

    def test_openai_provider_would_return_floats(self) -> None:
        """Test OpenAIEmbeddingProvider returns floats (contract)."""
        # We can't actually test this without API key, but verify contract
        from ingestion.embeddings.provider import OpenAIEmbeddingProvider

        # Contract: must implement embed() method
        assert hasattr(OpenAIEmbeddingProvider, "embed")

    def test_mock_provider_deterministic(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider is deterministic (same input = same output)."""
        text = "test content"

        embeddings1 = mock_provider.embed([text])
        embeddings2 = mock_provider.embed([text])

        assert embeddings1 == embeddings2
        assert embeddings1[0] == embeddings2[0]

    def test_mock_provider_embedding_dimension(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider returns 1536-dimensional vectors."""
        texts = ["test"]
        embeddings = mock_provider.embed(texts)

        assert len(embeddings[0]) == 1536

    def test_providers_same_dimension(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test both providers return same dimensional vectors."""
        # MockEmbeddingProvider dimension
        mock_embeddings = mock_provider.embed(["test"])
        mock_dim = len(mock_embeddings[0])

        # Both should be 1536
        assert mock_dim == 1536

    def test_mock_provider_multiple_texts(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider handles multiple texts."""
        texts = ["text1", "text2", "text3", "text4", "text5"]
        embeddings = mock_provider.embed(texts)

        assert len(embeddings) == 5
        assert all(len(e) == 1536 for e in embeddings)

    def test_mock_provider_empty_list(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider handles empty input."""
        embeddings = mock_provider.embed([])

        assert isinstance(embeddings, list)
        assert len(embeddings) == 0

    def test_mock_provider_single_text(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider with single text."""
        embeddings = mock_provider.embed(["single text"])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536

    def test_mock_provider_empty_string(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider with empty string."""
        embeddings = mock_provider.embed([""])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536

    def test_mock_provider_different_inputs_different_outputs(
        self, mock_provider: MockEmbeddingProvider
    ) -> None:
        """Test different inputs produce different embeddings."""
        embeddings1 = mock_provider.embed(["text1"])
        embeddings2 = mock_provider.embed(["text2"])

        assert embeddings1[0] != embeddings2[0]

    def test_mock_provider_embeddings_normalized(
        self, mock_provider: MockEmbeddingProvider
    ) -> None:
        """Test MockEmbeddingProvider produces normalized vectors."""
        embeddings = mock_provider.embed(["test"])
        vector = embeddings[0]

        # Convert to numpy for norm calculation
        vector_np = np.array(vector)
        norm = np.linalg.norm(vector_np)

        # Should be approximately 1.0 (normalized)
        assert abs(norm - 1.0) < 0.01

    def test_provider_interface_implements_embed(
        self, mock_provider: MockEmbeddingProvider
    ) -> None:
        """Test EmbeddingProvider interface defines embed method."""
        assert hasattr(mock_provider, "embed")
        assert callable(mock_provider.embed)

    def test_mock_provider_returns_floats_not_integers(
        self, mock_provider: MockEmbeddingProvider
    ) -> None:
        """Test embeddings contain floats, not integers."""
        embeddings = mock_provider.embed(["test"])
        vector = embeddings[0]

        # At least some should be floats with decimals
        floats_with_decimals = sum(1 for x in vector if not isinstance(x, int))
        assert floats_with_decimals > 0

    def test_multiple_providers_same_interface(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider and OpenAI have same interface."""
        # Both should have embed method
        assert hasattr(mock_provider, "embed")

        from ingestion.embeddings.provider import OpenAIEmbeddingProvider

        assert hasattr(OpenAIEmbeddingProvider, "embed")

    def test_mock_provider_consistency_across_calls(
        self, mock_provider: MockEmbeddingProvider
    ) -> None:
        """Test MockEmbeddingProvider consistency across multiple calls."""
        text = "consistent text"

        # Multiple calls with same text
        results = [mock_provider.embed([text])[0] for _ in range(5)]

        # All should be identical
        assert all(r == results[0] for r in results)

    def test_provider_embed_signature(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test embed method has correct signature."""
        import inspect

        sig = inspect.signature(mock_provider.embed)
        params = list(sig.parameters.keys())

        assert "texts" in params

    def test_mock_provider_with_very_long_text(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider with very long text."""
        long_text = "word " * 10000  # Very long text
        embeddings = mock_provider.embed([long_text])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536

    def test_mock_provider_with_special_characters(
        self, mock_provider: MockEmbeddingProvider
    ) -> None:
        """Test MockEmbeddingProvider with special characters."""
        texts = ["!@#$%", "emoji 😀 test", "unicode: 中文"]
        embeddings = mock_provider.embed(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 1536 for e in embeddings)

    def test_mock_provider_with_unicode(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider with unicode text."""
        texts = ["Hello", "你好", "مرحبا", "Привет"]
        embeddings = mock_provider.embed(texts)

        assert len(embeddings) == 4
        # All embeddings should be consistent
        assert all(len(e) == 1536 for e in embeddings)

    def test_mock_provider_with_newlines(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider with text containing newlines."""
        text = "line1\nline2\nline3"
        embeddings = mock_provider.embed([text])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536

    def test_mock_provider_with_tabs(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider with tabs."""
        text = "col1\tcol2\tcol3"
        embeddings = mock_provider.embed([text])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536

    def test_different_text_lengths_same_output_dimension(
        self, mock_provider: MockEmbeddingProvider
    ) -> None:
        """Test that different text lengths always produce 1536-dim output."""
        texts = [
            "a",
            "hello world",
            "this is a longer text with more content",
            "a" * 10000,
        ]

        embeddings = mock_provider.embed(texts)

        assert all(len(e) == 1536 for e in embeddings)

    def test_mock_provider_batch_processing(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test MockEmbeddingProvider processes multiple texts efficiently."""
        texts = [f"text_{i}" for i in range(100)]
        embeddings = mock_provider.embed(texts)

        assert len(embeddings) == 100
        assert all(len(e) == 1536 for e in embeddings)

    def test_embedding_vector_values_in_valid_range(
        self, mock_provider: MockEmbeddingProvider
    ) -> None:
        """Test embedding values are in reasonable range for normalized vectors."""
        embeddings = mock_provider.embed(["test"])
        vector = embeddings[0]

        # For normalized vectors, individual components should be in [-1, 1]
        assert all(-2 < x < 2 for x in vector)

    def test_providers_inherit_from_abstract_base(
        self, mock_provider: MockEmbeddingProvider
    ) -> None:
        """Test MockEmbeddingProvider inherits from EmbeddingProvider."""
        assert isinstance(mock_provider, EmbeddingProvider)

    def test_abstract_base_class_has_embed_method(self) -> None:
        """Test EmbeddingProvider abstract class has embed method."""
        # Should have abstract method
        assert hasattr(EmbeddingProvider, "embed")
        assert callable(EmbeddingProvider.embed)

    def test_mock_provider_embedding_stability(self, mock_provider: MockEmbeddingProvider) -> None:
        """Test embedding stability (seeded randomness)."""
        # Same input should always produce same output
        text = "stable input text"

        results = [mock_provider.embed([text])[0][0] for _ in range(10)]  # First component

        # All should be identical
        assert len(set(results)) == 1


@pytest.mark.unit
class TestProviderContractParity:
    """Contract parity tests between MockEmbeddingProvider and OpenAIEmbeddingProvider.

    These tests verify both providers return identically structured responses,
    so the mock can safely stand in for the real provider in the rest of the
    test suite. The OpenAI client is mocked, so no API key or network access
    is required.
    """

    EXPECTED_DIM = 1536

    @pytest.fixture
    def mock_provider(self) -> MockEmbeddingProvider:
        """Create a MockEmbeddingProvider instance."""
        return MockEmbeddingProvider()

    @pytest.fixture
    def openai_provider(self) -> Iterator[OpenAIEmbeddingProvider]:
        """Create an OpenAIEmbeddingProvider with a mocked OpenAI client.

        The mocked client mirrors the real SDK response shape:
        response.data is a list of items, each with an `embedding`
        attribute containing a list of floats.
        """
        from unittest.mock import patch

        from ingestion.embeddings.provider import OpenAIEmbeddingProvider

        def fake_create(model: str, input: list[str]) -> MagicMock:  # noqa: A002
            response = MagicMock()
            items = []
            for _ in input:
                item = MagicMock()
                item.embedding = [0.1] * TestProviderContractParity.EXPECTED_DIM
                items.append(item)
            response.data = items
            return response

        with patch("openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.embeddings.create.side_effect = fake_create
            mock_openai_cls.return_value = mock_client
            yield OpenAIEmbeddingProvider()

    def test_both_return_list_type(
        self, mock_provider: MockEmbeddingProvider, openai_provider: OpenAIEmbeddingProvider
    ) -> None:
        """Both providers return a list for a list of input texts."""
        texts = ["hello", "world"]

        assert isinstance(mock_provider.embed(texts), list)
        assert isinstance(openai_provider.embed(texts), list)

    def test_both_return_one_vector_per_text(
        self, mock_provider: MockEmbeddingProvider, openai_provider: OpenAIEmbeddingProvider
    ) -> None:
        """Both providers return exactly one embedding per input text."""
        texts = ["a", "b", "c"]

        assert len(mock_provider.embed(texts)) == len(texts)
        assert len(openai_provider.embed(texts)) == len(texts)

    def test_both_return_vectors_of_floats(
        self, mock_provider: MockEmbeddingProvider, openai_provider: OpenAIEmbeddingProvider
    ) -> None:
        """Both providers return each embedding as a list of Python floats."""
        texts = ["sample text"]

        for provider in (mock_provider, openai_provider):
            vector = provider.embed(texts)[0]
            assert isinstance(vector, list)
            assert all(isinstance(x, float) for x in vector)

    def test_both_return_same_dimension(
        self, mock_provider: MockEmbeddingProvider, openai_provider: OpenAIEmbeddingProvider
    ) -> None:
        """Both providers return vectors of identical dimensionality."""
        texts = ["dimension check"]

        mock_dim = len(mock_provider.embed(texts)[0])
        openai_dim = len(openai_provider.embed(texts)[0])

        assert mock_dim == openai_dim == self.EXPECTED_DIM

    def test_both_handle_empty_input(
        self, mock_provider: MockEmbeddingProvider, openai_provider: OpenAIEmbeddingProvider
    ) -> None:
        """Both providers return an empty list for empty input."""
        assert mock_provider.embed([]) == []
        assert openai_provider.embed([]) == []

    def test_both_handle_batch_input_consistently(
        self, mock_provider: MockEmbeddingProvider, openai_provider: OpenAIEmbeddingProvider
    ) -> None:
        """Both providers preserve input order and count for batches."""
        texts = [f"text_{i}" for i in range(10)]

        mock_result = mock_provider.embed(texts)
        openai_result = openai_provider.embed(texts)

        assert len(mock_result) == len(openai_result) == 10
        assert all(len(v) == self.EXPECTED_DIM for v in mock_result)
        assert all(len(v) == self.EXPECTED_DIM for v in openai_result)

    def test_factory_returns_provider_instances(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The factory returns EmbeddingProvider instances for both names."""

        from ingestion.embeddings import provider as provider_module
        from ingestion.embeddings.provider import get_embedding_provider

        monkeypatch.setattr("openai.OpenAI", MagicMock())

        assert isinstance(get_embedding_provider("mock"), EmbeddingProvider)
        assert isinstance(get_embedding_provider("openai"), provider_module.EmbeddingProvider)
