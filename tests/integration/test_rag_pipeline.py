"""Integration tests for the complete RAG pipeline."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from rag.generator.review_generator import ReviewConfig, ReviewGenerator
from rag.retriever.hybrid import HybridRetriever
from rag.retriever.keyword_search import KeywordSearcher
from rag.retriever.vector_store import VectorStore


def test_full_rag_pipeline_with_mock_llm(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run retrieval, reranking, generation, and parsing without a real LLM."""
    profile_id = "issue38"
    collection_name = f"profile_{profile_id}"

    chunks = [
        {
            "id": "fastapi-project",
            "text": (
                "Built a Python FastAPI REST API with automated pytest "
                "integration tests and PostgreSQL."
            ),
            "metadata": {
                "source_id": "portfolio-api",
                "chunk_index": 0,
                "section": "projects",
            },
        },
        {
            "id": "painting-project",
            "text": (
                "Created watercolor landscape paintings and displayed them "
                "in a community art exhibition."
            ),
            "metadata": {
                "source_id": "portfolio-art",
                "chunk_index": 0,
                "section": "projects",
            },
        },
        {
            "id": "cooking-project",
            "text": (
                "Developed a collection of vegetarian recipes and documented "
                "meal preparation techniques."
            ),
            "metadata": {
                "source_id": "portfolio-food",
                "chunk_index": 0,
                "section": "projects",
            },
        },
        {
            "id": "music-project",
            "text": (
                "Recorded acoustic guitar performances and organized a local " "music showcase."
            ),
            "metadata": {
                "source_id": "portfolio-music",
                "chunk_index": 0,
                "section": "projects",
            },
        },
    ]

    embeddings = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]

    vector_store = VectorStore(persist_dir=str(tmp_path / "chromadb"))
    collection = vector_store.get_collection(collection_name)

    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        embeddings=embeddings,
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
    )

    keyword_searcher = KeywordSearcher()
    keyword_searcher.index(chunks)

    retriever = HybridRetriever(
        vector_store=vector_store,
        keyword_searcher=keyword_searcher,
        vector_weight=0.7,
        keyword_weight=0.3,
    )

    query = "Python FastAPI API integration testing"
    query_embedding = [1.0, 0.0, 0.0, 0.0]

    retrieved_chunks = retriever.retrieve(
        query=query,
        profile_id=profile_id,
        query_embedding=query_embedding,
        max_chunks=2,
        min_score=0.0,
    )

    assert len(retrieved_chunks) == 2
    assert retrieved_chunks[0]["id"] == "fastapi-project"
    assert retrieved_chunks[0]["score"] >= retrieved_chunks[1]["score"]
    assert retrieved_chunks[0]["vector_score"] > 0
    assert retrieved_chunks[0]["keyword_score"] > 0

    mock_llm_output = json.dumps(
        {
            "skills_feedback": {
                "summary": (
                    "The portfolio demonstrates Python, FastAPI, pytest, "
                    "and PostgreSQL experience."
                ),
                "suggestions": [
                    "Add deployment details.",
                    "Document API performance results.",
                ],
            }
        }
    )

    mock_create = Mock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=mock_llm_output))]
        )
    )

    mock_llm_provider = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=mock_create))
    )

    generator = ReviewGenerator(
        ReviewConfig(
            api_key="test-key",
            base_url="https://example.invalid/v1",
            model="mock-model",
            temperature=0.0,
        )
    )

    monkeypatch.setattr(generator, "client", mock_llm_provider)

    feedback = generator.generate_section(
        section_name="skills_feedback",
        context_chunks=retrieved_chunks,
        profile_data={
            "github_username": "integration-test-user",
            "projects": [{"name": "FastAPI Portfolio API"}],
        },
    )

    mock_create.assert_called_once()

    request = mock_create.call_args.kwargs
    user_prompt = request["messages"][1]["content"]

    assert "Built a Python FastAPI REST API" in user_prompt
    assert "portfolio-api" in user_prompt
    assert request["model"] == "mock-model"
    assert request["temperature"] == 0.0

    assert feedback.section_name == "skills_feedback"
    assert feedback.confidence == 0.9
    assert feedback.suggestions == [
        "Add deployment details.",
        "Document API performance results.",
    ]

    parsed_content = json.loads(feedback.content)

    assert parsed_content["summary"] == (
        "The portfolio demonstrates Python, FastAPI, pytest, " "and PostgreSQL experience."
    )
