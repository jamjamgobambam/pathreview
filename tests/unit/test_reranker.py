import json
from unittest.mock import MagicMock

import pytest

from rag.retriever.reranker import MAX_CHUNK_CHARS_IN_PROMPT, Reranker


def mock_llm_response(content: str) -> MagicMock:
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content))]
    return response


@pytest.mark.unit
class TestReranker:

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def reranker(self, mock_client: MagicMock) -> Reranker:
        return Reranker(client=mock_client, model="test-model")

    def test_rerank_reorders_by_llm_score(self, reranker: Reranker, mock_client: MagicMock) -> None:
        mock_client.chat.completions.create.return_value = mock_llm_response(
            '{"c1": 0.1, "c2": 0.95}'
        )
        chunks = [
            {"id": "c1", "text": "a", "score": 0.9},
            {"id": "c2", "text": "b", "score": 0.5},
        ]

        result = reranker.rerank("some query", chunks)

        assert [c["id"] for c in result] == ["c2", "c1"]
        assert result[0]["score"] == 0.95

    def test_rerank_handles_fenced_json_block(
        self, reranker: Reranker, mock_client: MagicMock
    ) -> None:
        mock_client.chat.completions.create.return_value = mock_llm_response(
            '```json\n{"c1": 0.2, "c2": 0.8}\n```'
        )
        chunks = [
            {"id": "c1", "text": "a", "score": 0.5},
            {"id": "c2", "text": "b", "score": 0.5},
        ]

        result = reranker.rerank("query", chunks)

        assert result[0]["id"] == "c2"

    def test_rerank_falls_back_on_llm_error(
        self, reranker: Reranker, mock_client: MagicMock
    ) -> None:
        mock_client.chat.completions.create.side_effect = Exception("API down")
        chunks = [
            {"id": "c1", "text": "a", "score": 0.9},
            {"id": "c2", "text": "b", "score": 0.5},
        ]

        result = reranker.rerank("query", chunks)

        assert result == chunks

    def test_rerank_falls_back_on_unparseable_response(
        self, reranker: Reranker, mock_client: MagicMock
    ) -> None:
        mock_client.chat.completions.create.return_value = mock_llm_response("this is not json")
        chunks = [
            {"id": "c1", "text": "a", "score": 0.9},
            {"id": "c2", "text": "b", "score": 0.5},
        ]

        result = reranker.rerank("query", chunks)

        assert result == chunks

    def test_rerank_empty_chunks_skips_llm_call(
        self, reranker: Reranker, mock_client: MagicMock
    ) -> None:
        result = reranker.rerank("query", [])

        assert result == []
        mock_client.chat.completions.create.assert_not_called()

    def test_rerank_respects_top_k(self, reranker: Reranker, mock_client: MagicMock) -> None:
        chunks = [{"id": f"c{i}", "text": "x", "score": 0.5} for i in range(5)]
        mock_client.chat.completions.create.return_value = mock_llm_response(
            json.dumps({f"c{i}": 1.0 - i * 0.1 for i in range(5)})
        )

        result = reranker.rerank("query", chunks, top_k=2)

        assert len(result) == 2
        assert result[0]["id"] == "c0"

    def test_missing_chunk_id_in_scores_keeps_original_score(
        self, reranker: Reranker, mock_client: MagicMock
    ) -> None:
        mock_client.chat.completions.create.return_value = mock_llm_response('{"c1": 0.9}')
        chunks = [
            {"id": "c1", "text": "a", "score": 0.2},
            {"id": "c2", "text": "b", "score": 0.7},
        ]

        result = reranker.rerank("query", chunks)

        c2 = next(c for c in result if c["id"] == "c2")
        assert c2["score"] == 0.7

    def test_llm_called_with_low_temperature_and_configured_model(
        self, reranker: Reranker, mock_client: MagicMock
    ) -> None:
        mock_client.chat.completions.create.return_value = mock_llm_response('{"c1": 0.5}')
        chunks = [{"id": "c1", "text": "a", "score": 0.5}]

        reranker.rerank("query", chunks)

        _, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["temperature"] == 0.0
        assert kwargs["model"] == "test-model"

    def test_build_prompt_truncates_long_chunk_text(self, reranker: Reranker) -> None:
        long_text = "a" * 1000
        chunks = [{"id": "c1", "text": long_text, "score": 0.5}]

        prompt = reranker._build_prompt("query", chunks)

        assert "a" * (MAX_CHUNK_CHARS_IN_PROMPT + 1) not in prompt
