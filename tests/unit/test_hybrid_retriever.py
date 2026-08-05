"""Tests for the HybridRetriever interface in rag/retriever/hybrid.py"""

import pytest

from rag.retriever.hybrid import HybridRetriever


@pytest.mark.unit
class TestHybridRetrieverInterface:
    """Interface tests for HybridRetriever."""

    def test_init_exists_with_documented_default_weights(self):
        """HybridRetriever can be constructed and applies the documented default weights."""
        retriever = HybridRetriever(vector_store=None, keyword_searcher=None)

        assert retriever.vector_weight == 0.7
        assert retriever.keyword_weight == 0.3

    def test_retrieve_method_exists(self):
        """HybridRetriever exposes a callable retrieve method."""
        assert callable(getattr(HybridRetriever, "retrieve", None))
