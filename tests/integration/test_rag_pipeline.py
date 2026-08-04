"""Integration test for the full RAG pipeline against a mock LLM.

Issue #38: Wire HybridRetriever → ReviewGenerator → EvalSuite together
end-to-end using mocked external dependencies (ChromaDB, OpenAI) so the
test runs offline without any API keys or running services.
"""

import json
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from rag.evaluator.eval_suite import EvalSuite
from rag.generator.output_parser import FeedbackSection
from rag.generator.review_generator import ReviewConfig, ReviewGenerator
from rag.retriever.hybrid import HybridRetriever
from rag.retriever.keyword_search import KeywordSearcher

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

FIXTURE_CHUNKS = [
    {
        "id": "chunk_001",
        "text": "Strong Python skills demonstrated through multiple FastAPI projects.",
        "metadata": {"source_id": "resume_001", "chunk_index": 0, "section": "skills"},
    },
    {
        "id": "chunk_002",
        "text": "Built a REST API with PostgreSQL and Docker for a weather forecasting app.",
        "metadata": {"source_id": "readme_001", "chunk_index": 0, "section": "projects"},
    },
    {
        "id": "chunk_003",
        "text": "Portfolio lacks tests and CI/CD configuration in most repositories.",
        "metadata": {"source_id": "readme_002", "chunk_index": 1, "section": "gaps"},
    },
]

SAMPLE_PROFILE = {
    "github_username": "janedoe",
    "projects": ["weather-app", "portfolio-site"],
}

# A minimal JSON response that output_parser._parse_json_output can handle.
# Each top-level key becomes a FeedbackSection.section_name.
MOCK_LLM_RESPONSE = json.dumps(
    {
        "skills_feedback": {
            "content": "Good Python and FastAPI skills visible across projects.",
            "suggestions": ["Add type hints throughout", "Include test coverage badge"],
        },
        "projects_feedback": {
            "content": "Weather app shows real-world API integration.",
            "suggestions": ["Add a live demo link", "Document setup steps"],
        },
        "presentation_feedback": {
            "content": "READMEs are present but brief.",
            "suggestions": ["Expand usage section"],
        },
        "gaps_feedback": {
            "content": "No CI/CD configuration found.",
            "suggestions": ["Add GitHub Actions workflow"],
        },
        "first_impression": {
            "content": "Solid early-career portfolio with room to grow.",
            "suggestions": [],
        },
    }
)

# Fake 3-dimensional query embedding (dimensionality doesn't matter for mocks)
FAKE_QUERY_EMBEDDING = [0.1, 0.2, 0.3]


# ---------------------------------------------------------------------------
# Helper: build a mocked VectorStore that returns FIXTURE_CHUNKS
# ---------------------------------------------------------------------------


def _make_mock_vector_store(chunks: list[dict] = FIXTURE_CHUNKS) -> MagicMock:
    """Return a MagicMock VectorStore whose query() and get_collection() both
    return data shaped like the real ChromaDB responses."""

    mock_vs = MagicMock()

    # vector_store.query() return value
    mock_vs.query.return_value = [
        {
            "id": c["id"],
            "text": c["text"],
            "metadata": c["metadata"],
            "score": 0.85,
        }
        for c in chunks
    ]

    # collection.get() return value used by HybridRetriever._get_all_chunks()
    mock_collection = MagicMock()
    mock_collection.get.return_value = {
        "ids": [c["id"] for c in chunks],
        "documents": [c["text"] for c in chunks],
        "metadatas": [c["metadata"] for c in chunks],
    }
    mock_vs.get_collection.return_value = mock_collection

    return mock_vs


# ---------------------------------------------------------------------------
# Stage 1 — Retrieval
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestRetrievalStage:
    """HybridRetriever returns correctly shaped results from mocked sources."""

    def test_retrieve_returns_list_of_dicts(self) -> None:
        """retrieve() must return a non-empty list."""
        keyword_searcher = KeywordSearcher()
        keyword_searcher.index(FIXTURE_CHUNKS)

        retriever = HybridRetriever(
            vector_store=_make_mock_vector_store(),
            keyword_searcher=keyword_searcher,
        )

        results = retriever.retrieve(
            query="Python skills projects",
            profile_id="test_profile",
            query_embedding=FAKE_QUERY_EMBEDDING,
        )

        assert isinstance(results, list)
        assert len(results) > 0

    def test_retrieve_result_shape(self) -> None:
        """Every result must have id, text, metadata, and score keys."""
        keyword_searcher = KeywordSearcher()
        keyword_searcher.index(FIXTURE_CHUNKS)

        retriever = HybridRetriever(
            vector_store=_make_mock_vector_store(),
            keyword_searcher=keyword_searcher,
        )

        results = retriever.retrieve(
            query="Python skills",
            profile_id="test_profile",
            query_embedding=FAKE_QUERY_EMBEDDING,
        )

        for result in results:
            assert "id" in result
            assert "text" in result
            assert "metadata" in result
            assert "score" in result
            assert isinstance(result["score"], float)
            assert 0.0 <= result["score"] <= 1.0


# ---------------------------------------------------------------------------
# Stage 2 — Generation
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestGenerationStage:
    """ReviewGenerator returns FeedbackSections from a mocked LLM response."""

    @pytest.fixture
    def generator(self) -> Generator[ReviewGenerator, None, None]:
        """Construct ReviewGenerator with a patched OpenAI client."""
        config = ReviewConfig(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="mock-model",
        )
        with patch("rag.generator.review_generator.openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            mock_client.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content=MOCK_LLM_RESPONSE))]
            )
            gen = ReviewGenerator(config)
            yield gen

    def test_generate_full_review_returns_list(self, generator: ReviewGenerator) -> None:
        """generate_full_review() must return a non-empty list."""
        sections = generator.generate_full_review(SAMPLE_PROFILE, FIXTURE_CHUNKS)
        assert isinstance(sections, list)
        assert len(sections) > 0

    def test_generate_full_review_returns_feedback_sections(
        self, generator: ReviewGenerator
    ) -> None:
        """Every item must be a FeedbackSection with non-empty content."""
        sections = generator.generate_full_review(SAMPLE_PROFILE, FIXTURE_CHUNKS)
        for section in sections:
            assert isinstance(section, FeedbackSection)
            assert isinstance(section.section_name, str)
            assert len(section.section_name) > 0
            assert isinstance(section.content, str)
            assert len(section.content) > 0
            assert isinstance(section.confidence, float)
            assert 0.0 <= section.confidence <= 1.0

    def test_generate_full_review_no_duplicate_section_names(
        self, generator: ReviewGenerator
    ) -> None:
        """_consolidate_feedback must remove duplicate section names."""
        sections = generator.generate_full_review(SAMPLE_PROFILE, FIXTURE_CHUNKS)
        names = [s.section_name for s in sections]
        assert len(names) == len(set(names)), "Duplicate section names found"


# ---------------------------------------------------------------------------
# Stage 3 — Evaluation
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestEvaluationStage:
    """EvalSuite scores are in [0, 1] and overall = mean(relevance, faithfulness)."""

    @pytest.fixture
    def eval_suite(self) -> EvalSuite:
        """Return a fresh EvalSuite instance."""
        return EvalSuite()

    def test_eval_scores_in_range(self, eval_suite: EvalSuite) -> None:
        """All three scores must be between 0.0 and 1.0."""
        feedback = "Strong Python skills. Good use of FastAPI and PostgreSQL projects."
        result = eval_suite.run(
            query="Python skills projects",
            chunks=FIXTURE_CHUNKS,
            feedback=feedback,
        )
        assert 0.0 <= result.relevance_score <= 1.0
        assert 0.0 <= result.faithfulness_score <= 1.0
        assert 0.0 <= result.overall_score <= 1.0

    def test_eval_overall_is_mean_of_components(self, eval_suite: EvalSuite) -> None:
        """overall_score must equal (relevance + faithfulness) / 2."""
        feedback = "Strong Python skills. Good use of FastAPI and PostgreSQL projects."
        result = eval_suite.run(
            query="Python skills projects",
            chunks=FIXTURE_CHUNKS,
            feedback=feedback,
        )
        expected = (result.relevance_score + result.faithfulness_score) / 2
        assert abs(result.overall_score - expected) < 1e-9


# ---------------------------------------------------------------------------
# Full end-to-end pipeline
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestFullRAGPipeline:
    """Exercise all three stages in sequence, asserting the boundary contracts."""

    def test_full_pipeline_happy_path(self) -> None:
        """Retriever → Generator → Evaluator all succeed with valid mock data."""
        # --- Stage 1: Retrieval ---
        keyword_searcher = KeywordSearcher()
        keyword_searcher.index(FIXTURE_CHUNKS)

        retriever = HybridRetriever(
            vector_store=_make_mock_vector_store(),
            keyword_searcher=keyword_searcher,
        )

        retrieved_chunks = retriever.retrieve(
            query="Python skills projects REST API",
            profile_id="test_profile",
            query_embedding=FAKE_QUERY_EMBEDDING,
        )

        assert len(retrieved_chunks) > 0, "Retrieval returned no chunks"

        # --- Stage 2: Generation ---
        config = ReviewConfig(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="mock-model",
        )

        with patch("rag.generator.review_generator.openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            mock_client.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content=MOCK_LLM_RESPONSE))]
            )

            generator = ReviewGenerator(config)
            sections = generator.generate_full_review(SAMPLE_PROFILE, retrieved_chunks)

        assert len(sections) > 0, "Generator returned no sections"
        assert all(isinstance(s, FeedbackSection) for s in sections)

        # --- Stage 3: Evaluation ---
        eval_suite = EvalSuite()
        combined_feedback = " ".join(s.content for s in sections)

        result = eval_suite.run(
            query="Python skills projects REST API",
            chunks=retrieved_chunks,
            feedback=combined_feedback,
        )

        assert 0.0 <= result.relevance_score <= 1.0
        assert 0.0 <= result.faithfulness_score <= 1.0
        assert 0.0 <= result.overall_score <= 1.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestEdgeCases:
    """Pipeline behaviour under abnormal inputs."""

    def test_empty_retrieval_generator_still_returns_sections(self) -> None:
        """Generator must not crash when given zero retrieved chunks.

        Each section should fall back to an error message rather than raising.
        """
        config = ReviewConfig(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="mock-model",
        )

        with patch("rag.generator.review_generator.openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            mock_client.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content=MOCK_LLM_RESPONSE))]
            )
            generator = ReviewGenerator(config)
            sections = generator.generate_full_review(SAMPLE_PROFILE, [])  # empty chunks

        assert isinstance(sections, list)
        assert len(sections) > 0
        for section in sections:
            assert isinstance(section, FeedbackSection)
            assert len(section.content) > 0

    def test_malformed_json_falls_back_to_plaintext_section(self) -> None:
        """When the mock LLM returns invalid JSON, output_parser must fall back
        to _parse_plaintext_output and still return a FeedbackSection."""
        config = ReviewConfig(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="mock-model",
        )

        malformed_response = "This is not JSON at all. Just plain advice about your portfolio."

        with patch("rag.generator.review_generator.openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            mock_client.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content=malformed_response))]
            )
            generator = ReviewGenerator(config)
            sections = generator.generate_full_review(SAMPLE_PROFILE, FIXTURE_CHUNKS)

        assert isinstance(sections, list)
        assert len(sections) > 0
        # Plaintext fallback names the section "general_feedback"
        section_names = [s.section_name for s in sections]
        assert "general_feedback" in section_names

    def test_empty_retrieval_eval_returns_zero_scores(self) -> None:
        """EvalSuite must return 0.0 for all scores when chunks list is empty."""
        eval_suite = EvalSuite()
        result = eval_suite.run(
            query="Python skills",
            chunks=[],
            feedback="Some feedback text.",
        )
        assert result.relevance_score == 0.0
        assert result.faithfulness_score == 0.0
        assert result.overall_score == 0.0
