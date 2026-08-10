"""Tests for hybrid.py"""

from collections.abc import Callable
from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever
from rag.retriever.keyword_search import KeywordSearcher

BuildRetriever = Callable[[list[dict], dict[str, float]], HybridRetriever]


@pytest.mark.unit
class TestHybridRetriever:
    """Test suite for HybridRetriever."""

    @pytest.fixture
    def vector_store(self) -> Mock:
        """Vector store stub returning hand-picked similarity scores.

        HybridRetriever._get_all_chunks() calls vector_store.get_collection(),
        so that needs a minimal valid response even though its return value is
        never used (see the keyword_searcher note in build_retriever below).
        """
        store = Mock()
        store.get_collection.return_value.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }
        return store

    @pytest.fixture
    def build_retriever(self, vector_store: Mock) -> BuildRetriever:
        """Build a HybridRetriever wired to a pre-indexed KeywordSearcher.

        retrieve() never calls keyword_searcher.index() itself (a separate
        gap from issue #24), so tests index it manually to exercise the
        blending logic in isolation.
        """

        def _build(chunks: list[dict], vector_scores: dict[str, float]) -> HybridRetriever:
            vector_store.query.return_value = [
                {"id": c["id"], "text": c["text"], "metadata": {}, "score": vector_scores[c["id"]]}
                for c in chunks
            ]
            keyword_searcher = KeywordSearcher()
            keyword_searcher.index(chunks)
            return HybridRetriever(vector_store, keyword_searcher)

        return _build

    def test_relevant_chunk_outranks_keyword_stuffed_irrelevant_chunk(
        self, build_retriever: BuildRetriever
    ) -> None:
        """Issue #24 regression: a chunk stuffed with technology names should
        not outrank a chunk that is genuinely relevant to the query, just
        because it repeats the query's tech names more often.

        Reproduction: a resume chunk that actually describes the
        candidate's Python/React work (highest possible vector similarity)
        must outrank an unrelated README chunk that just lists tech names
        repeatedly (inflated BM25 score), even at the default
        vector_weight=0.7 / keyword_weight=0.3 split.
        """
        chunks = [
            {
                "id": "resume_1",
                "text": (
                    "Led backend architecture for a fintech platform, owning the "
                    "migration from a monolith to services built in Python, with "
                    "a customer dashboard built in React."
                ),
            },
            {
                "id": "resume_2",
                "text": (
                    "Managed a team of four engineers and ran quarterly planning "
                    "for the platform roadmap, prioritizing reliability work over "
                    "new features."
                ),
            },
            {
                "id": "readme_1",
                "text": (
                    "Tech stack Python React Python React Docker Python React "
                    "PostgreSQL Python React"
                ),
            },
            {
                "id": "readme_2",
                "text": (
                    "This project has no license and is not accepting contributions at this time"
                ),
            },
        ]
        vector_scores = {
            "resume_1": 1.0,  # most relevant chunk gets the highest vector score
            "resume_2": 0.8,
            "readme_1": 0.85,  # shares vocabulary with the query, but isn't relevant
            "readme_2": 0.5,
        }

        retriever = build_retriever(chunks, vector_scores)

        results = retriever.retrieve(
            query="What is this candidate's Python and React experience?",
            profile_id="test",
            query_embedding=[1.0, 0.0, 0.0],
            max_chunks=10,
            min_score=0.0,
        )

        top_id = results[0]["id"]
        assert top_id == "resume_1", (
            f"expected the genuinely relevant resume chunk to rank first, "
            f"but {top_id!r} ranked first instead -- keyword score is "
            f"over-weighting the tech-name-stuffed chunk (issue #24)"
        )

    def test_keyword_match_breaks_a_near_tied_vector_ranking(
        self, build_retriever: BuildRetriever
    ) -> None:
        """RRF must not collapse into vector-only ranking: a chunk containing
        an exact, rare identifier the query asks about should still win over
        a chunk with merely similar generic phrasing and a slightly higher
        vector score.
        """
        chunks = [
            {
                "id": "match",
                "text": (
                    "Implemented libsodium encryption to secure session tokens "
                    "across the platform."
                ),
            },
            {
                "id": "rival",
                "text": (
                    "Built a secure session token system using industry standard "
                    "cryptography libraries."
                ),
            },
            {
                "id": "filler_1",
                "text": "Optimized database queries to reduce checkout latency significantly.",
            },
            {
                "id": "filler_2",
                "text": "Led migration of the CI pipeline to a new build system.",
            },
            {
                "id": "filler_3",
                "text": "Wrote integration tests covering payment retry logic.",
            },
        ]
        vector_scores = {
            "rival": 0.78,  # generic phrasing embeds slightly closer to the query
            "match": 0.75,  # the actual answer -- a close second by vector alone
            "filler_1": 0.5,
            "filler_2": 0.4,
            "filler_3": 0.3,
        }

        retriever = build_retriever(chunks, vector_scores)

        results = retriever.retrieve(
            query="What experience does this candidate have with libsodium for encryption?",
            profile_id="test",
            query_embedding=[1.0, 0.0, 0.0],
            max_chunks=10,
            min_score=0.0,
        )

        top_id = results[0]["id"]
        assert top_id == "match", (
            f"expected the chunk with the exact rare-term match to rank first, "
            f"but {top_id!r} ranked first instead"
        )

    def test_tied_scores_break_deterministically_by_id(
        self, build_retriever: BuildRetriever
    ) -> None:
        """Chunks tied on both vector and keyword score must sort in the same
        deterministic order across repeated calls, rather than depending on
        Python's hash-randomized set/dict iteration order for string ids.
        """
        chunks = [
            {"id": "c", "text": "alpha bravo charlie"},
            {"id": "a", "text": "delta echo foxtrot"},
            {"id": "b", "text": "golf hotel india"},
        ]
        vector_scores = {"a": 0.5, "b": 0.5, "c": 0.5}

        retriever = build_retriever(chunks, vector_scores)

        def run() -> list[str]:
            results = retriever.retrieve(
                query="totally different subject matter entirely",
                profile_id="test",
                query_embedding=[1.0, 0.0, 0.0],
                max_chunks=10,
                min_score=0.0,
            )
            return [r["id"] for r in results]

        first_run = run()
        second_run = run()

        assert first_run == second_run == ["a", "b", "c"]
