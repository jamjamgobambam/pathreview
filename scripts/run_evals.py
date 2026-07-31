"""Run the RAG evaluation suite against benchmark portfolios.

Loads a set of benchmark portfolios from tests/fixtures/sample_profiles/,
runs each through the full RAG pipeline (retrieval, generation, evaluation)
using mock providers so it runs offline with no API key or network access,
and writes a JSON report of quality scores to eval_results.json.
"""

import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import structlog

from core.config import settings
from ingestion.embeddings.provider import EmbeddingProvider, get_embedding_provider
from rag.evaluator.eval_suite import EvalSuite
from rag.generator.mock_generator import MockReviewGenerator
from rag.retriever.hybrid import HybridRetriever
from rag.retriever.keyword_search import KeywordSearcher
from rag.retriever.vector_store import VectorStore

logger = structlog.get_logger()

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_profiles"
OUTPUT_PATH = Path(__file__).parent.parent / "eval_results.json"

# Mock embeddings are random per-text vectors, not semantically meaningful,
# so a real similarity threshold would filter out valid results. Use 0.0
# for offline eval so retrieval always returns chunks.
MOCK_MIN_SCORE = 0.0


def load_fixtures() -> list[dict]:
    """Load all benchmark portfolio fixtures.

    Returns:
        List of fixture dicts, one per benchmark portfolio
    """
    fixtures = []
    for path in sorted(FIXTURES_DIR.glob("*.json")):
        with open(path) as f:
            fixtures.append(json.load(f))
    return fixtures


def index_fixture(
    fixture: dict, vector_store: VectorStore, embedding_provider: EmbeddingProvider
) -> tuple[KeywordSearcher, list[float]]:
    """Embed and index a fixture's chunks into the vector store and a keyword index.

    Args:
        fixture: Fixture dict with profile_id, query, and chunks
        vector_store: VectorStore to insert chunks into
        embedding_provider: Provider used to embed chunk text and the query

    Returns:
        Tuple of (indexed KeywordSearcher, query embedding)
    """
    profile_id = fixture["profile_id"]
    chunks = fixture["chunks"]
    texts = [c["text"] for c in chunks]

    embeddings = embedding_provider.embed(texts)
    query_embedding = embedding_provider.embed([fixture["query"]])[0]

    ids = [f"{profile_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"source_id": c["source_id"], "chunk_index": i, "section": c.get("section", "")}
        for i, c in enumerate(chunks)
    ]

    # Insert directly via the collection rather than VectorStore.add_chunks,
    # which expects Chunk objects with attributes (chunk.id, chunk.source_id)
    # that don't match the actual Chunk dataclass (text, metadata only).
    # See PLAN.md risks: add_chunks is dead code and not used here.
    collection = vector_store.get_collection(f"profile_{profile_id}")
    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    keyword_chunks = [
        {"id": ids[i], "text": texts[i], "metadata": metadatas[i]} for i in range(len(chunks))
    ]
    keyword_searcher = KeywordSearcher()
    keyword_searcher.index(keyword_chunks)

    return keyword_searcher, query_embedding


def evaluate_fixture(fixture: dict, vector_store: VectorStore, embedding_provider: EmbeddingProvider) -> dict:
    """Run one fixture through retrieval, generation, and evaluation.

    Args:
        fixture: Fixture dict with profile_id, query, github_username, projects, chunks
        vector_store: Shared VectorStore instance
        embedding_provider: Shared embedding provider

    Returns:
        Dict with profile_id and eval scores, or an error entry on failure
    """
    profile_id = fixture["profile_id"]
    try:
        keyword_searcher, query_embedding = index_fixture(fixture, vector_store, embedding_provider)
        retriever = HybridRetriever(vector_store, keyword_searcher)
        retrieved_chunks = retriever.retrieve(
            query=fixture["query"],
            profile_id=profile_id,
            query_embedding=query_embedding,
            max_chunks=10,
            min_score=MOCK_MIN_SCORE,
        )

        profile_data = {
            "github_username": fixture.get("github_username", ""),
            "projects": fixture.get("projects", []),
        }
        generator = MockReviewGenerator()
        sections = generator.generate_full_review(profile_data, retrieved_chunks)
        feedback_text = "\n".join(s.content for s in sections)

        eval_suite = EvalSuite()
        result = eval_suite.run(fixture["query"], retrieved_chunks, feedback_text)

        return {
            "profile_id": profile_id,
            "relevance_score": result.relevance_score,
            "faithfulness_score": result.faithfulness_score,
            "overall_score": result.overall_score,
            "chunks_retrieved": len(retrieved_chunks),
            "sections_generated": len(sections),
        }
    except Exception as e:
        # A single bad fixture should not stop the whole run.
        logger.error("fixture_evaluation_failed", profile_id=profile_id, error=str(e))
        return {"profile_id": profile_id, "error": str(e)}


def main() -> None:
    """Execute the full evaluation pipeline and output results."""
    print("Running RAG evaluation suite...")

    fixtures = load_fixtures()
    if not fixtures:
        print(f"No fixtures found in {FIXTURES_DIR}")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp_dir:
        vector_store = VectorStore(persist_dir=tmp_dir)
        embedding_provider = get_embedding_provider(settings.llm_provider)

        results = [
            evaluate_fixture(fixture, vector_store, embedding_provider) for fixture in fixtures
        ]

    scored = [r for r in results if "overall_score" in r]
    failed = [r for r in results if "error" in r]
    average_overall_score = sum(r["overall_score"] for r in scored) / len(scored) if scored else 0.0

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "profiles_evaluated": len(scored),
        "profiles_failed": len(failed),
        "average_overall_score": round(average_overall_score, 4),
        "results": results,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Evaluation complete. Results written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
