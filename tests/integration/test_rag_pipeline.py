"""Integration tests for the full RAG pipeline.

Issue #38: unit tests exist for individual RAG components (retrieval,
reranking, generation, parsing) but nothing verifies they work together
end-to-end. This exercises a real query through all four stages, using a
mock LLM client in place of the OpenAI API (no live network calls).

Note: there is no standalone "reranker" module in rag/ (see docs/JOURNAL.md).
HybridRetriever.retrieve() blends and re-sorts vector + keyword scores in a
single step, so that blend/sort *is* the reranking stage here.
"""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ingestion.embeddings.provider import MockEmbeddingProvider
from rag.generator.review_generator import ReviewConfig, ReviewGenerator
from rag.retriever.hybrid import HybridRetriever
from rag.retriever.keyword_search import KeywordSearcher
from rag.retriever.vector_store import VectorStore

PROFILE_ID = "test-profile"


def _line_chunks(text: str, source_id: str) -> list[dict]:
    """Split a fixture text into naive line-level chunks for the corpus."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    return [
        {"id": f"{source_id}-{i}", "text": line, "metadata": {"source_id": source_id}}
        for i, line in enumerate(lines)
    ]


@pytest.fixture
def corpus(sample_resume_text, sample_readme_text) -> list[dict]:
    """Retrieval corpus built from the shared resume/README fixtures, tagged by source."""
    return _line_chunks(sample_resume_text, "resume") + _line_chunks(sample_readme_text, "readme")


# One canned chat-completion payload per section, in the order
# ReviewGenerator.generate_full_review() requests them.
SECTION_PAYLOADS = [
    json.dumps(
        {"skills_feedback": {"key_skills": ["Python", "FastAPI"], "suggestions": ["Learn Rust"]}}
    ),
    json.dumps({"projects_feedback": {"project_quality_score": 0.8, "suggestions": ["Add tests"]}}),
    json.dumps({"presentation_feedback": {"readme_quality": 0.9, "suggestions": []}}),
    json.dumps(
        {
            "gaps_feedback": {
                "missing_high_demand_skills": ["Kubernetes"],
                "suggestions": ["Learn K8s"],
            }
        }
    ),
    # first_impression's template asks for plain text, no JSON.
    "Strong full-stack candidate with solid Python and React experience.",
]


def _mock_llm_client(payloads: list[str]) -> SimpleNamespace:
    """A minimal stand-in for the openai client, returning canned content per call in sequence."""
    responses = [
        SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=p))])
        for p in payloads
    ]
    create = Mock(side_effect=responses)
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


@pytest.mark.integration
def test_full_rag_pipeline_retrieval_to_parsed_output(tmp_path, corpus) -> None:
    """Runs retrieval -> reranking -> generation -> parsing end-to-end and checks the output."""
    embedder = MockEmbeddingProvider()

    # --- Retrieval + reranking setup ---
    vector_store = VectorStore(persist_dir=str(tmp_path))
    collection = vector_store.get_collection(f"profile_{PROFILE_ID}")
    collection.upsert(
        ids=[c["id"] for c in corpus],
        embeddings=embedder.embed([c["text"] for c in corpus]),
        documents=[c["text"] for c in corpus],
        metadatas=[c["metadata"] for c in corpus],
    )

    keyword_searcher = KeywordSearcher()
    keyword_searcher.index(corpus)

    retriever = HybridRetriever(vector_store, keyword_searcher)
    query = "What Python backend experience does this candidate have?"
    query_embedding = embedder.embed([query])[0]

    retrieved_chunks = retriever.retrieve(
        query, PROFILE_ID, query_embedding, max_chunks=5, min_score=0.0
    )

    assert retrieved_chunks, "retrieval + reranking returned no chunks"
    scores = [r["score"] for r in retrieved_chunks]
    assert scores == sorted(scores, reverse=True)
    # BM25 keyword signal should rank the Python resume line first (mock embeddings
    # carry no real semantic similarity).
    assert retrieved_chunks[0]["metadata"]["source_id"] == "resume"
    assert "python" in retrieved_chunks[0]["text"].lower()

    # --- Generation + parsing ---
    generator = ReviewGenerator(
        ReviewConfig(api_key="test", base_url="http://mock.invalid", model="mock-model")
    )
    generator.client = _mock_llm_client(SECTION_PAYLOADS)

    profile_data = {"github_username": "janedoe", "projects": [{"name": "weather-app"}]}
    sections = generator.generate_full_review(profile_data, retrieved_chunks)

    assert generator.client.chat.completions.create.call_count == 5
    assert [s.section_name for s in sections] == [
        "skills_feedback",
        "projects_feedback",
        "presentation_feedback",
        "gaps_feedback",
        "general_feedback",  # plaintext fallback names itself, not "first_impression"
    ]
    for section in sections:
        assert section.content
        assert 0.0 <= section.confidence <= 1.0
        # Citations are appended from the retrieved chunks' source_id metadata.
        assert "Sources:" in section.content
