## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview's RAG system uses hybrid retrieval (vector similarity plus BM25 keyword search), but `docs/ARCHITECTURE.md` only mentions that at a high level. It does not explain how the two scores are normalized, what the default weights are, or how a final blended score is computed. That makes it hard for contributors to understand why certain chunks rank higher than others or how to tune retrieval. A successful fix would document the scoring logic from `rag/retriever/hybrid.py` in `ARCHITECTURE.md`, including default weights (`vector_weight=0.7`, `keyword_weight=0.3`), the `min_score` threshold, and a short worked example.

**"Is this right for me?" checklist reasoning:**
- Scope is Tier 1 / docs-only: mainly `docs/ARCHITECTURE.md`, with reading `rag/retriever/hybrid.py` for accuracy.
- I can explain the gap in my own words (missing formula + weights, not a runtime crash).
- Success is clear: architecture docs include formula, defaults, and an example.
- Fits my current skill level for a first contribution to a multi-service AI codebase; low risk of scope creep into agent/frontend work.
- I claimed the issue on GitHub and can finish a PR within the Module 3 timeline.

**Branch name:** docs/36-hybrid-retrieval-scoring

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
