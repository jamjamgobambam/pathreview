"""Integration tests for the full RAG pipeline.

Issue #38: unit tests exist for individual RAG components (retrieval,
reranking, generation, parsing) but nothing verifies they work together
end-to-end. This stub documents that gap; it will be replaced with a real
test in the implementation PR.
"""

import pytest


@pytest.mark.xfail(reason="Issue #38: no RAG pipeline integration test exists yet", strict=True)
def test_full_rag_pipeline_not_yet_implemented() -> None:
    pytest.fail(
        "No test currently runs for retrieval -> reranking -> generation -> parsing end-to-end."
    )
