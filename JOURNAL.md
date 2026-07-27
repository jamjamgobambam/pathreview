## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The current RAG retriever relies solely on vector and keyword similarity for ranking documents. This issue proposes adding an LLM-based re-ranking step to evaluate and score the relevance of retrieved chunks before they are sent to the generator. Implementing this feature in the `rag/retriever` component will improve the overall quality and accuracy of the context used for generation.

**Branch name:** feat/34-llm-reranker

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/hangolehai/pathreview/commit/866ac24

**Reproduction summary:**
I verified the codebase currently only uses vector and keyword similarity in `rag/retriever/hybrid.py`. I added a TODO comment in the `retrieve` method exactly where the new LLM re-ranking step needs to be inserted before it returns the `final_results`.

**PLAN.md link:** https://github.com/hangolehai/pathreview/blob/feat/34-llm-reranker/PLAN.md

**Walkthrough video (recommended):** [Skipped for now]

**Blockers or open questions:**
None at the moment. The plan is solid and I understand where the changes need to be made.