# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/38

**Issue title:** Add an integration test that runs the full RAG pipeline against a mock LLM

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview has unit tests for individual RAG components, but it does not have an integration test proving that those components work together for a complete query. The missing coverage spans retrieval, reranking, LLM-backed generation, and parsing into structured feedback. A successful test will exercise that full path with a mock LLM so it remains deterministic, avoids external API calls, and can run reliably in automated test environments. The work belongs in `tests/integration/test_rag_pipeline.py` and will verify the contracts between several modules rather than testing them only in isolation.

**Selection notes — “Is this right for me?” checklist:**
- The expected outcome and relevant test file are clearly identified, so the issue has a bounded deliverable.
- The issue is appropriately labeled Tier 2 because it requires tracing data across multiple RAG modules, not changing just one isolated function.
- The 4–6 hour estimate is manageable, and the test can use mocks instead of requiring paid credentials or live LLM calls.
- I can inspect the existing retrieval, generation, parsing, and test-fixture patterns before implementing the integration test and ask maintainers for clarification if the intended mock LLM provider is unclear.
- The change can be verified locally with a focused integration test and the repository’s standard checks, giving it a clear definition of done.

**Branch name:** `test/38-rag-pipeline-integration-test`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [202d0fe](https://github.com/vrajhm/pathreview/commit/202d0feb83f2ad681d18e8975e5087081d1e893e)

**Reproduction summary:**
I ran `pytest --collect-only -q tests/integration` and observed `no tests
collected in 0.01s` because the integration-test package contains no test
module. Tracing the RAG code confirmed that retrieval/ranking, generation, and
parsing exist as separate components but are never exercised together with a
mock LLM.

**PLAN.md link:** [PLAN.md](https://github.com/vrajhm/pathreview/blob/test/38-rag-pipeline-integration-test/PLAN.md)

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
The issue calls out reranking, but the current codebase has no standalone
reranker; the plan treats hybrid score blending and sorting in
`rag/retriever/hybrid.py` as that stage. The local shell also lacks project
dependencies, so the full suite currently stops during collection and must be
rerun in the configured development environment.
