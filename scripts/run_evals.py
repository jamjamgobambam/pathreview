"""Run the RAG evaluation suite against benchmark portfolios.

Loads curated profiles from tests/fixtures/sample_profiles/, runs ingest →
retrieve → generate → EvalSuite scoring, and writes eval_results.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ingestion.chunking.strategy_selector import StrategySelector
from ingestion.embeddings.batch_processor import BatchEmbeddingProcessor
from ingestion.embeddings.provider import get_embedding_provider
from rag.evaluator.eval_suite import EvalSuite
from rag.generator.output_parser import FeedbackSection
from rag.generator.review_generator import ReviewConfig, ReviewGenerator
from rag.retriever.hybrid import HybridRetriever
from rag.retriever.keyword_search import KeywordSearcher
from rag.retriever.vector_store import VectorStore

DEFAULT_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "sample_profiles"
DEFAULT_OUTPUT = REPO_ROOT / "eval_results.json"

SECTION_NAMES = [
    "skills_feedback",
    "projects_feedback",
    "presentation_feedback",
    "gaps_feedback",
    "first_impression",
]


def load_portfolios(fixtures_dir: Path) -> list[dict[str, Any]]:
    """Load all JSON portfolio fixtures from a directory."""
    if not fixtures_dir.is_dir():
        raise FileNotFoundError(f"Fixtures directory not found: {fixtures_dir}")

    portfolios: list[dict[str, Any]] = []
    for path in sorted(fixtures_dir.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        data.setdefault("id", path.stem)
        portfolios.append(data)

    if not portfolios:
        raise FileNotFoundError(f"No portfolio JSON files in {fixtures_dir}")
    return portfolios


def _sanitize_metadata(metadata: dict) -> dict:
    """Chroma only accepts str/int/float/bool metadata values."""
    clean: dict[str, Any] = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        elif value is None:
            continue
        else:
            clean[key] = str(value)
    return clean


def ingest_portfolio(
    profile: dict[str, Any],
    collection,
    embedding_provider,
) -> int:
    """Chunk and embed resume + project READMEs into a Chroma collection."""
    selector = StrategySelector()
    processor = BatchEmbeddingProcessor(embedding_provider, collection)
    profile_id = str(profile["id"])
    total_chunks = 0

    resume_text = profile.get("resume_text", "")
    if resume_text.strip():
        source_id = f"resume_{profile_id}"
        metadata = _sanitize_metadata(
            {
                "source_id": source_id,
                "profile_id": profile_id,
                "filename": profile.get("resume_filename", "resume.md"),
                "source_type": "resume",
            }
        )
        chunks = selector.chunk(resume_text, metadata)
        for chunk in chunks:
            chunk.metadata = _sanitize_metadata(chunk.metadata)
        processor.process(chunks)
        total_chunks += len(chunks)

    for project in profile.get("projects", []):
        readme = project.get("readme", "")
        if not readme.strip():
            continue
        repo_name = project.get("name", "project")
        source_id = f"readme_{profile_id}_{repo_name}"
        metadata = _sanitize_metadata(
            {
                "source_id": source_id,
                "profile_id": profile_id,
                "repo_name": repo_name,
                "source_type": "readme",
            }
        )
        chunks = selector.chunk(readme, metadata)
        for chunk in chunks:
            chunk.metadata = _sanitize_metadata(chunk.metadata)
        processor.process(chunks)
        total_chunks += len(chunks)

    return total_chunks


def mock_generate_review(
    profile_data: dict[str, Any],
    retrieved_chunks: list[dict],
) -> list[FeedbackSection]:
    """Deterministic review grounded in retrieved chunks (no API key)."""
    username = profile_data.get("github_username", "candidate")
    context_bits = [
        chunk.get("text", "").strip().replace("\n", " ")[:180]
        for chunk in retrieved_chunks[:5]
        if chunk.get("text", "").strip()
    ]
    context_summary = " ".join(context_bits) if context_bits else "limited portfolio context"

    suggestions_by_section = {
        "skills_feedback": [
            "Add impact metrics next to each listed skill on the resume.",
            "Include one concrete project example for your strongest skill.",
        ],
        "projects_feedback": [
            "Expand each README with problem statement, tech stack, and results.",
            "Highlight measurable outcomes such as latency or user counts.",
        ],
        "presentation_feedback": [
            "Rewrite the portfolio intro to lead with your strongest project.",
            "Link GitHub repos clearly from the resume and project pages.",
        ],
        "gaps_feedback": [
            "Consider documenting testing and deployment practices.",
            "Add a short case study that shows end-to-end ownership.",
        ],
        "first_impression": [
            "Update the first-screen summary to quantify your recent work.",
            "Provide a clear call-to-action linking to your best repository.",
        ],
    }

    sections: list[FeedbackSection] = []
    for section_name in SECTION_NAMES:
        suggestions = suggestions_by_section[section_name]
        content = (
            f"For {username}, the {section_name.replace('_', ' ')} review draws on "
            f"portfolio evidence: {context_summary}. "
            f"You should {suggestions[0].lower().rstrip('.')}."
        )
        sections.append(
            FeedbackSection(
                section_name=section_name,
                content=content,
                confidence=0.75,
                suggestions=suggestions,
            )
        )
    return sections


def sections_to_feedback_text(sections: list[FeedbackSection]) -> str:
    """Flatten feedback sections into a single text blob for scoring."""
    parts: list[str] = []
    for section in sections:
        parts.append(section.content)
        for suggestion in section.suggestions:
            parts.append(f"- {suggestion}")
    return "\n".join(parts)


def generate_review(
    profile_data: dict[str, Any],
    retrieved_chunks: list[dict],
    llm_provider: str,
) -> list[FeedbackSection]:
    """Generate review sections via mock helper or ReviewGenerator."""
    if llm_provider == "mock":
        return mock_generate_review(profile_data, retrieved_chunks)

    from core.config import settings

    api_key = settings.openai_api_key or settings.openrouter_api_key
    if not api_key:
        raise RuntimeError(
            "LLM_PROVIDER is not mock but no OpenAI/OpenRouter API key is configured"
        )

    if settings.openrouter_api_key and not settings.openai_api_key:
        config = ReviewConfig(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
        )
    else:
        config = ReviewConfig(
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
        )

    return ReviewGenerator(config).generate_full_review(profile_data, retrieved_chunks)


def evaluate_portfolio(
    profile: dict[str, Any],
    embedding_provider_name: str,
    llm_provider: str,
) -> dict[str, Any]:
    """Run full RAG + eval pipeline for one portfolio fixture."""
    profile_id = str(profile["id"])
    query = profile.get(
        "eval_query",
        "Review this portfolio for skills, projects, and presentation",
    )

    with tempfile.TemporaryDirectory(prefix=f"pathreview_eval_{profile_id}_") as tmp:
        vector_store = VectorStore(persist_dir=tmp)
        collection_name = f"profile_{profile_id}"
        collection = vector_store.get_collection(collection_name)

        embedding_provider = get_embedding_provider(embedding_provider_name)
        chunk_count = ingest_portfolio(profile, collection, embedding_provider)

        query_embedding = embedding_provider.embed([query])[0]
        retriever = HybridRetriever(vector_store, KeywordSearcher())
        # Mock embeddings are hash-based; keep min_score low so hybrid can return hits
        chunks = retriever.retrieve(
            query=query,
            profile_id=profile_id,
            query_embedding=query_embedding,
            max_chunks=10,
            min_score=0.0,
        )

        if not chunks:
            # Fallback: use all ingested docs so scoring still runs
            chunks = retriever._get_all_chunks(collection_name)

        profile_data = {
            "github_username": profile.get("github_username", ""),
            "projects": profile.get("projects", []),
            "resume_text": profile.get("resume_text", ""),
        }
        sections = generate_review(profile_data, chunks, llm_provider)
        feedback = sections_to_feedback_text(sections)

        result = EvalSuite().run(query, chunks, feedback)

        return {
            "id": profile_id,
            "github_username": profile.get("github_username", ""),
            "chunk_count": chunk_count,
            "retrieved_count": len(chunks),
            "relevance_score": round(result.relevance_score, 4),
            "faithfulness_score": round(result.faithfulness_score, 4),
            "actionability_score": round(result.actionability_score, 4),
            "overall_score": round(result.overall_score, 4),
        }


def build_report(portfolio_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-portfolio scores into a summary report."""
    n = len(portfolio_results)
    if n == 0:
        return {
            "summary": {
                "portfolio_count": 0,
                "avg_relevance_score": 0.0,
                "avg_faithfulness_score": 0.0,
                "avg_actionability_score": 0.0,
                "avg_overall_score": 0.0,
            },
            "portfolios": [],
        }

    def avg(key: str) -> float:
        return round(sum(item[key] for item in portfolio_results) / n, 4)

    return {
        "summary": {
            "portfolio_count": n,
            "avg_relevance_score": avg("relevance_score"),
            "avg_faithfulness_score": avg("faithfulness_score"),
            "avg_actionability_score": avg("actionability_score"),
            "avg_overall_score": avg("overall_score"),
        },
        "portfolios": portfolio_results,
    }


def main(argv: list[str] | None = None) -> int:
    """Execute the full evaluation pipeline and write eval_results.json."""
    parser = argparse.ArgumentParser(description="Run PathReview offline RAG evals")
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=DEFAULT_FIXTURES,
        help="Directory of benchmark portfolio JSON files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for eval_results.json",
    )
    args = parser.parse_args(argv)

    llm_provider = os.getenv("LLM_PROVIDER", "mock").lower()
    embedding_provider = "mock" if llm_provider == "mock" else "openai"

    print("Running RAG evaluation suite...")
    portfolios = load_portfolios(args.fixtures_dir)
    results = [
        evaluate_portfolio(profile, embedding_provider, llm_provider)
        for profile in portfolios
    ]
    report = build_report(results)

    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        f"Evaluated {summary['portfolio_count']} portfolios | "
        f"avg overall={summary['avg_overall_score']:.3f} "
        f"(relevance={summary['avg_relevance_score']:.3f}, "
        f"faithfulness={summary['avg_faithfulness_score']:.3f}, "
        f"actionability={summary['avg_actionability_score']:.3f})"
    )
    print(f"Evaluation complete. Results written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
