"""Tests for the LLM-based chunk reranker (issue #34)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from rag.retriever.reranker import ChunkReranker, RerankerConfig


@pytest.fixture
def config() -> RerankerConfig:
    return RerankerConfig(
        api_key="test-key",
        base_url="http://localhost:8000",
        model="test-model",
        relevance_threshold=3.0,
        batch_size=10,
    )


@pytest.fixture
def reranker(config: RerankerConfig) -> ChunkReranker:
    return ChunkReranker(config)


@pytest.fixture
def sample_chunks() -> list[dict]:
    return [
        {
            "id": "chunk_1",
            "text": "Built a dashboard using React and Tailwind CSS.",
            "metadata": {"source_id": "resume_projects"},
            "score": 0.82,
        },
        {
            "id": "chunk_2",
            "text": "Deployed a Flask REST API framework on AWS Lambda.",
            "metadata": {"source_id": "resume_experience"},
            "score": 0.71,
        },
        {
            "id": "chunk_3",
            "text": "Looking for a role in a modern framework-driven team.",
            "metadata": {"source_id": "cover_letter"},
            "score": 0.65,
        },
        {
            "id": "chunk_4",
            "text": "Created a Vue.js single-page application with Vuex.",
            "metadata": {"source_id": "github_readme"},
            "score": 0.61,
        },
    ]


class TestChunkRerankerImport:
    """Verify the reranker module is importable and integrated."""

    def test_reranker_module_importable(self) -> None:
        from rag.retriever.reranker import ChunkReranker  # noqa: F401

    def test_hybrid_retriever_accepts_reranker_param(self) -> None:
        import inspect

        from rag.retriever.hybrid import HybridRetriever

        sig = inspect.signature(HybridRetriever.__init__)
        params = list(sig.parameters.keys())
        assert "reranker" in params


class TestRerankerRerank:
    """Test the rerank method with mocked LLM responses."""

    def test_empty_chunks_returns_empty(self, reranker: ChunkReranker) -> None:
        result = reranker.rerank("some query", [])
        assert result == []

    def test_reranks_by_llm_score(self, reranker: ChunkReranker, sample_chunks: list[dict]) -> None:
        llm_response = json.dumps(
            [
                {"index": 0, "score": 9.0},
                {"index": 1, "score": 2.0},
                {"index": 2, "score": 1.0},
                {"index": 3, "score": 8.0},
            ]
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = llm_response

        with patch.object(reranker.client.chat.completions, "create", return_value=mock_response):
            result = reranker.rerank("What frontend frameworks?", sample_chunks)

        assert result[0]["id"] == "chunk_1"
        assert result[1]["id"] == "chunk_4"
        assert len(result) == 2  # chunks 2 and 3 below threshold of 3.0

    def test_respects_top_k(self, reranker: ChunkReranker, sample_chunks: list[dict]) -> None:
        llm_response = json.dumps(
            [
                {"index": 0, "score": 9.0},
                {"index": 1, "score": 7.0},
                {"index": 2, "score": 6.0},
                {"index": 3, "score": 8.0},
            ]
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = llm_response

        with patch.object(reranker.client.chat.completions, "create", return_value=mock_response):
            result = reranker.rerank("query", sample_chunks, top_k=2)

        assert len(result) == 2
        assert result[0]["rerank_score"] >= result[1]["rerank_score"]

    def test_falls_back_on_api_error(
        self, reranker: ChunkReranker, sample_chunks: list[dict]
    ) -> None:
        import openai

        with patch.object(
            reranker.client.chat.completions,
            "create",
            side_effect=openai.APIError(message="rate limit", request=MagicMock(), body=None),
        ):
            result = reranker.rerank("query", sample_chunks)

        # Falls back to original scores; all above threshold
        assert len(result) > 0
        for chunk in result:
            assert "rerank_score" in chunk

    def test_handles_malformed_json_gracefully(
        self, reranker: ChunkReranker, sample_chunks: list[dict]
    ) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not valid json at all"

        with patch.object(reranker.client.chat.completions, "create", return_value=mock_response):
            result = reranker.rerank("query", sample_chunks)

        assert len(result) > 0


class TestHybridRetrieverWithReranker:
    """Test that HybridRetriever passes results through the reranker."""

    def test_retrieve_calls_reranker_when_provided(self) -> None:

        from rag.retriever.hybrid import HybridRetriever

        mock_vs = MagicMock()
        mock_ks = MagicMock()
        mock_reranker = MagicMock()

        mock_vs.query.return_value = [{"id": "c1", "text": "hello", "metadata": {}, "score": 0.9}]
        mock_vs.get_collection.return_value.get.return_value = {
            "ids": ["c1"],
            "documents": ["hello"],
            "metadatas": [{}],
        }
        mock_ks.search.return_value = []
        mock_reranker.rerank.return_value = [
            {"id": "c1", "text": "hello", "metadata": {}, "score": 0.9, "rerank_score": 8.0}
        ]

        retriever = HybridRetriever(mock_vs, mock_ks, reranker=mock_reranker)
        result = retriever.retrieve("test", "prof1", [0.1, 0.2])

        mock_reranker.rerank.assert_called_once()
        assert result[0]["rerank_score"] == 8.0

    def test_retrieve_works_without_reranker(self) -> None:
        from rag.retriever.hybrid import HybridRetriever

        mock_vs = MagicMock()
        mock_ks = MagicMock()

        mock_vs.query.return_value = [{"id": "c1", "text": "hello", "metadata": {}, "score": 0.9}]
        mock_vs.get_collection.return_value.get.return_value = {
            "ids": ["c1"],
            "documents": ["hello"],
            "metadatas": [{}],
        }
        mock_ks.search.return_value = []

        retriever = HybridRetriever(mock_vs, mock_ks)
        result = retriever.retrieve("test", "prof1", [0.1, 0.2])

        assert len(result) >= 1
        assert "rerank_score" not in result[0]
