"""Tests for the LLM-based chunk reranker (issue #34).

This file demonstrates the gap: the hybrid retriever has no reranking step.
Chunks go directly from blended scoring to the generator without any semantic
relevance check. These tests define the expected behavior of the reranker
that needs to be implemented.
"""

import pytest


class TestRerankerExists:
    """Reproduction: verify that no reranker module exists yet."""

    def test_reranker_module_importable(self) -> None:
        """The reranker module should be importable from rag.retriever.

        This test currently FAILS, proving the issue is real:
        there is no reranking step between retrieval and generation.
        """
        try:
            from rag.retriever.reranker import ChunkReranker  # noqa: F401

            assert True
        except ImportError:
            pytest.fail(
                "rag.retriever.reranker.ChunkReranker does not exist yet. "
                "Issue #34: no LLM re-ranking step is implemented."
            )

    def test_hybrid_retriever_has_no_reranker_param(self) -> None:
        """The hybrid retriever currently has no reranker integration point."""
        import inspect

        from rag.retriever.hybrid import HybridRetriever

        sig = inspect.signature(HybridRetriever.__init__)
        params = list(sig.parameters.keys())
        assert (
            "reranker" not in params
        ), "reranker param already exists — issue may already be partially fixed"
