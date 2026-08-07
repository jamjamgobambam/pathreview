"""Tests for the LLM re-ranking stage (rag/retriever/reranker.py)."""

import pytest

from rag.retriever.reranker import (
    LLMReranker,
    MockReranker,
    RerankConfig,
    Reranker,
    get_reranker,
)

# ---------------------------------------------------------------------------
# Fake OpenAI-compatible client for exercising LLMReranker without a network.
# ---------------------------------------------------------------------------


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content=None, exc=None):
        self._content = content
        self._exc = exc
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        return _FakeResponse(self._content)


class _FakeChat:
    def __init__(self, content=None, exc=None):
        self.completions = _FakeCompletions(content=content, exc=exc)


class FakeClient:
    """Minimal stand-in for ``openai.OpenAI`` used by LLMReranker."""

    def __init__(self, content=None, exc=None):
        self.chat = _FakeChat(content=content, exc=exc)


def make_chunks(*ids: str) -> list[dict]:
    """Build a list of chunk dicts with distinct text per id."""
    return [{"id": i, "text": f"text for {i}", "score": 0.5} for i in ids]


@pytest.fixture
def config() -> RerankConfig:
    return RerankConfig(api_key="test-key", base_url="http://test", model="test-model")


# ---------------------------------------------------------------------------
# MockReranker
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMockReranker:
    """Deterministic, network-free reranker behavior."""

    def test_empty_returns_empty(self):
        assert MockReranker().rerank("q", [], top_k=5) == []

    def test_single_chunk_returned_as_is(self):
        chunks = make_chunks("a")
        result = MockReranker().rerank("q", chunks, top_k=5)
        assert [c["id"] for c in result] == ["a"]

    def test_single_chunk_not_scored(self):
        """The 0/1 short-circuit skips scoring entirely."""
        chunks = make_chunks("a")
        result = MockReranker().rerank("q", chunks, top_k=5)
        assert "rerank_score" not in result[0]

    def test_all_chunks_get_scores(self):
        chunks = make_chunks("a", "b", "c")
        result = MockReranker().rerank("q", chunks, top_k=5)
        assert all("rerank_score" in c for c in result)

    def test_output_is_permutation_of_input(self):
        chunks = make_chunks("a", "b", "c", "d")
        result = MockReranker().rerank("q", chunks, top_k=10)
        assert sorted(c["id"] for c in result) == ["a", "b", "c", "d"]

    def test_deterministic_across_calls(self):
        chunks = make_chunks("a", "b", "c", "d", "e")
        rr = MockReranker()
        first = [c["id"] for c in rr.rerank("q", chunks, top_k=5)]
        second = [c["id"] for c in rr.rerank("q", chunks, top_k=5)]
        assert first == second

    def test_respects_top_k(self):
        chunks = make_chunks("a", "b", "c", "d", "e")
        result = MockReranker().rerank("q", chunks, top_k=2)
        assert len(result) == 2

    def test_scores_sorted_descending(self):
        chunks = make_chunks("a", "b", "c", "d")
        result = MockReranker().rerank("q", chunks, top_k=10)
        scores = [c["rerank_score"] for c in result]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# LLMReranker
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLLMReranker:
    """LLM-driven reranking with an injected fake client."""

    def test_reorders_by_llm_scores(self, config):
        # Incoming order a, b, c; LLM says c > a > b.
        chunks = make_chunks("a", "b", "c")
        client = FakeClient(content='{"a": 5, "b": 1, "c": 9}')
        result = LLMReranker(config, client=client).rerank("q", chunks, top_k=3)
        assert [c["id"] for c in result] == ["c", "a", "b"]

    def test_attaches_rerank_score(self, config):
        chunks = make_chunks("a", "b")
        client = FakeClient(content='{"a": 7, "b": 2}')
        result = LLMReranker(config, client=client).rerank("q", chunks, top_k=2)
        assert result[0]["rerank_score"] == 7.0
        assert result[1]["rerank_score"] == 2.0

    def test_respects_top_k(self, config):
        chunks = make_chunks("a", "b", "c", "d")
        client = FakeClient(content='{"a": 1, "b": 2, "c": 3, "d": 4}')
        result = LLMReranker(config, client=client).rerank("q", chunks, top_k=2)
        assert [c["id"] for c in result] == ["d", "c"]

    def test_missing_id_defaults_to_zero_and_sorts_last(self, config):
        chunks = make_chunks("a", "b", "c")
        # LLM omits "c"; it should default to 0 and rank last.
        client = FakeClient(content='{"a": 4, "b": 8}')
        result = LLMReranker(config, client=client).rerank("q", chunks, top_k=3)
        assert [c["id"] for c in result] == ["b", "a", "c"]
        assert result[-1]["rerank_score"] == 0.0

    def test_parses_json_wrapped_in_prose(self, config):
        chunks = make_chunks("a", "b")
        client = FakeClient(content='Here are the scores:\n```json\n{"a": 2, "b": 9}\n```\nDone.')
        result = LLMReranker(config, client=client).rerank("q", chunks, top_k=2)
        assert [c["id"] for c in result] == ["b", "a"]

    def test_malformed_json_falls_back_to_input_order(self, config):
        chunks = make_chunks("a", "b", "c")
        client = FakeClient(content="not json at all")
        result = LLMReranker(config, client=client).rerank("q", chunks, top_k=3)
        assert [c["id"] for c in result] == ["a", "b", "c"]

    def test_empty_content_falls_back_to_input_order(self, config):
        chunks = make_chunks("a", "b")
        client = FakeClient(content=None)
        result = LLMReranker(config, client=client).rerank("q", chunks, top_k=2)
        assert [c["id"] for c in result] == ["a", "b"]

    def test_client_exception_falls_back_to_input_order(self, config):
        chunks = make_chunks("a", "b", "c")
        client = FakeClient(exc=RuntimeError("API down"))
        result = LLMReranker(config, client=client).rerank("q", chunks, top_k=3)
        assert [c["id"] for c in result] == ["a", "b", "c"]

    def test_empty_returns_empty_without_calling_llm(self, config):
        client = FakeClient(content='{"a": 1}')
        result = LLMReranker(config, client=client).rerank("q", [], top_k=5)
        assert result == []
        assert client.chat.completions.calls == []

    def test_single_chunk_returned_without_calling_llm(self, config):
        client = FakeClient(content='{"a": 1}')
        chunks = make_chunks("a")
        result = LLMReranker(config, client=client).rerank("q", chunks, top_k=5)
        assert [c["id"] for c in result] == ["a"]
        assert client.chat.completions.calls == []

    def test_passes_model_and_temperature_to_client(self, config):
        chunks = make_chunks("a", "b")
        client = FakeClient(content='{"a": 1, "b": 2}')
        LLMReranker(config, client=client).rerank("q", chunks, top_k=2)
        call = client.chat.completions.calls[0]
        assert call["model"] == "test-model"
        assert call["temperature"] == 0.0


# ---------------------------------------------------------------------------
# get_reranker factory
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetReranker:
    def test_mock_provider_returns_mock_reranker(self):
        assert isinstance(get_reranker("mock"), MockReranker)

    def test_mock_provider_case_insensitive(self):
        assert isinstance(get_reranker("  MOCK  "), MockReranker)

    def test_real_provider_returns_llm_reranker(self, config):
        assert isinstance(get_reranker("openai", config), LLMReranker)

    def test_real_provider_without_config_raises(self):
        with pytest.raises(ValueError):
            get_reranker("openai")

    def test_returned_rerankers_are_reranker_instances(self, config):
        assert isinstance(get_reranker("mock"), Reranker)
        assert isinstance(get_reranker("openai", config), Reranker)
