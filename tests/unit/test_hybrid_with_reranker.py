"""Tests for hybrid.py + reranker.py wired together end-to-end.

Confirms issue #34's fix: when a Reranker is configured, HybridRetriever
widens its candidate pool and defers the final ranking to the LLM, correcting
the keyword-stuffing bias demonstrated in tests/unit/test_hybrid_keyword_bias.py.
"""

import json
from unittest.mock import Mock, patch

import pytest

from rag.retriever.hybrid import HybridRetriever
from rag.retriever.keyword_search import KeywordSearcher
from rag.retriever.reranker import Reranker, RerankerConfig


def _make_llm_response(content: str) -> Mock:
    response = Mock()
    response.choices = [Mock(message=Mock(content=content))]
    return response


@pytest.mark.unit
class TestHybridRetrieverWithReranker:
    """End-to-end: HybridRetriever + Reranker together fix the keyword-bias ranking."""

    @pytest.fixture
    def chunks(self) -> list[dict]:
        """Same corpus as test_hybrid_keyword_bias.py."""
        return [
            {
                "id": "stuffed",
                "text": (
                    "kubernetes kubernetes kubernetes kubernetes kubernetes kubernetes "
                    "pizza toppings recipe with extra cheese"
                ),
                "metadata": {"source_id": "s1"},
            },
            {
                "id": "relevant",
                "text": "our team migrated the payment service to a managed kubernetes cluster",
                "metadata": {"source_id": "s2"},
            },
            {
                "id": "filler1",
                "text": "built a responsive marketing website using react and tailwind css",
                "metadata": {"source_id": "s3"},
            },
            {
                "id": "filler2",
                "text": "wrote unit tests and integration tests for the billing microservice",
                "metadata": {"source_id": "s4"},
            },
            {
                "id": "filler3",
                "text": "designed a rest api for the mobile app backend using flask",
                "metadata": {"source_id": "s5"},
            },
        ]

    @pytest.fixture
    def mock_vector_store(self, chunks: list[dict]) -> Mock:
        store = Mock()
        store.query.return_value = [
            {
                "id": "relevant",
                "text": chunks[1]["text"],
                "metadata": chunks[1]["metadata"],
                "score": 0.9,
            },
            {
                "id": "stuffed",
                "text": chunks[0]["text"],
                "metadata": chunks[0]["metadata"],
                "score": 0.75,
            },
        ]
        collection = Mock()
        collection.get.return_value = {
            "ids": [c["id"] for c in chunks],
            "documents": [c["text"] for c in chunks],
            "metadatas": [c["metadata"] for c in chunks],
        }
        store.get_collection.return_value = collection
        return store

    @pytest.fixture
    def reranker(self) -> Reranker:
        config = RerankerConfig(
            api_key="test-key", base_url="https://example.invalid/v1", model="test-model"
        )
        with patch("rag.retriever.reranker.openai.OpenAI"):
            r = Reranker(config)
        r.client.chat.completions.create.return_value = _make_llm_response(
            json.dumps({"relevant": 0.95, "stuffed": 0.1})
        )
        return r

    def test_reranker_fixes_keyword_stuffing_bias_end_to_end(
        self, mock_vector_store: Mock, reranker: Reranker
    ) -> None:
        """Without a reranker, "stuffed" outranks "relevant" (see
        test_hybrid_keyword_bias.py). With one wired in, HybridRetriever
        widens its candidate pool and the LLM's judgment wins instead."""
        retriever = HybridRetriever(mock_vector_store, KeywordSearcher(), reranker=reranker)

        results = retriever.retrieve(
            query="kubernetes deployment",
            profile_id="profile1",
            query_embedding=[0.1, 0.2, 0.3],
            max_chunks=2,
            min_score=0.0,
        )

        assert [r["id"] for r in results] == ["relevant", "stuffed"]
        assert results[0]["rerank_score"] == 0.95

    def test_without_reranker_bias_still_reproduces(self, mock_vector_store: Mock) -> None:
        """Sanity check: the same setup, minus the reranker, still shows the
        original bug -- confirming the fix is what flips the outcome above,
        not some other change to the corpus/mocks."""
        retriever = HybridRetriever(mock_vector_store, KeywordSearcher())

        results = retriever.retrieve(
            query="kubernetes deployment",
            profile_id="profile1",
            query_embedding=[0.1, 0.2, 0.3],
            max_chunks=2,
            min_score=0.0,
        )

        assert [r["id"] for r in results] == ["stuffed", "relevant"]
