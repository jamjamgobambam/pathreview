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

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/qhowery/pathreview/commit/294b35fd7bcdd717ecde3dd492bebc539411bd9a

**Reproduction summary:**
I confirmed the documentation gap locally: `docs/ARCHITECTURE.md` only mentions hybrid retrieval at a high level, while `rag/retriever/hybrid.py` implements max-normalization, default weights `0.7` / `0.3`, blending, and `min_score=0.3`. I captured steps in `docs/issue-36-reproduction.md` and added three failing unit tests that assert the missing doc content — they fail today and should pass after the Week 9 doc fix.

**PLAN.md link:** https://github.com/qhowery/pathreview/blob/docs/36-hybrid-retrieval-scoring/PLAN.md

**Walkthrough video (recommended):** _(optional — add Loom link if recorded)_

**Blockers or open questions:**
In `HybridRetriever.retrieve`, `_get_all_chunks` is fetched but I don’t yet see an `index(...)` call before `keyword_searcher.search` — out of scope for this docs issue, but I may ask in office hours whether the keyword channel is empty in practice so the architecture prose stays accurate.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented PLAN.md sub-tasks 1–3: drafted the Hybrid retrieval scoring subsection in `docs/ARCHITECTURE.md` (max-normalization, default weights `0.7` / `0.3`, blend formula, `min_score`, worked example, code pointers). Confirmed the Week 8 acceptance tests in `tests/unit/test_architecture_hybrid_docs.py` now pass (3/3).

**Next steps:**
Self-review against CONTRIBUTING.md, open/finalize the PR to `ascherj/pathreview`, fill the PR template (including pre-existing `make check` / `make test-unit` failures note), and complete Check-in 2.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/295

**Branch:** `docs/36-hybrid-retrieval-scoring`

**What you built:**
Documented PathReview’s hybrid retrieval scoring in `docs/ARCHITECTURE.md`: how vector and BM25 scores are max-normalized, blended with default weights `vector_weight=0.7` / `keyword_weight=0.3`, filtered by `min_score=0.3`, sorted, and truncated — with a worked numeric example and pointers to `rag/retriever/hybrid.py`.

**Tests added or updated:**
- `tests/unit/test_architecture_hybrid_docs.py` (added in Week 8 as failing reproduction; now passing) — asserts ARCHITECTURE.md documents weights, normalization/blend formula, and `min_score`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes  
*(Full-repo `make check` / `make test-unit` still show pre-existing failures unrelated to #36; my changes introduce no new failures. Targeted: `pytest tests/unit/test_architecture_hybrid_docs.py` → 3 passed; ruff/black clean on that file. Documented in the PR.)*

**Draft PR feedback received from:** none
