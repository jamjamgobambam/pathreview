## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
PathReview's RAG pipeline currently ranks retrieved document chunks using a hybrid of vector similarity and BM25 keyword scores. While this approach is fast, it treats all high-scoring chunks equally without understanding whether each chunk actually answers the user's query. The issue proposes adding an optional re-ranking pass where a smaller LLM scores each retrieved chunk's relevance to the query before the top-k chunks are forwarded to the generator. The fix lives in `rag/retriever/`, adding a new `reranker.py` module and wiring it into `hybrid.py`. A successful implementation would improve answer quality on queries where the initial retrieval returns plausible but off-topic chunks.

**Is this right for me? — checklist reasoning:**
- The change is scoped to `rag/retriever/` with a clear interface boundary (existing `hybrid.py` retriever), so I can understand the full blast radius without reading the entire codebase.
- The new `reranker.py` will follow the same pattern as existing tools/parsers in the project, making the structure predictable.
- The LLM call is optional (re-ranking is a pass-through if disabled), so I can stub it and get tests passing before wiring up a real model.
- Estimated effort is 7–10 hours, which fits the module timeline.

**Branch name:** feat/34-llm-reranker

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit — to be updated after push]

**Reproduction summary:**
Added `tests/unit/test_reranker.py` with 6 failing tests that document the expected interface for `LLMReranker`. All 6 fail because `rag/retriever/reranker.py` does not exist and `HybridRetriever.__init__` has no `reranker` parameter — confirming the feature gap is real and precisely located.

**PLAN.md link:** [link to PLAN.md — to be updated after push]

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Need to confirm whether the project has a shared LLM client factory in `agent/orchestrator.py` that `LLMReranker` should reuse, or whether it should accept a raw `openai.OpenAI` client like `ReviewGenerator` does.
