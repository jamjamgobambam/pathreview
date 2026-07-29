"""Integration test for the full RAG pipeline against a mock LLM.

Issue #38: No integration test exists that exercises the full pipeline
(retriever → generator → evaluator) end-to-end. This file documents
the gap — the test below is intentionally marked xfail until implemented.
"""

import pytest


@pytest.mark.integration
@pytest.mark.xfail(reason="Issue #38: full RAG pipeline integration test not yet implemented")
def test_full_rag_pipeline_not_yet_implemented() -> None:
    """Placeholder confirming the integration test gap described in issue #38.

    The full pipeline wires together:
      HybridRetriever → ReviewGenerator (mock LLM) → EvalSuite

    None of these are exercised together in any existing test.
    See tests/unit/ for isolated component tests.
    """
    raise NotImplementedError(
        "Integration test for full RAG pipeline does not exist yet (issue #38)"
    )
