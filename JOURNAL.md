## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The documentation for `ARCHITECTURE.md` does not have additional detail apart from architecture: Hybrid retrieval (vector similarity + BM25 keyword). A successful fix should elaborate on the scoring formula used, and the heuristic behind the scoring formula. It affects  `docs/ARCHITECTURE.md` only, to explain the folder  `rag`, which includes `hybrid.py`, `keyword_search.py`, and `vector_store.py`.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

PR message:

docs(rag): include hybrid retrieval scoring formula for the RAG system.

docs/ARCHITECTURE.md does not have additional detail apart from architecture: Hybrid retrieval (vector similarity + BM25 keyword). Does not elaborate how the vector similarity is calculated, and what BM25 keyword is used. Added mathematical formulas + explanation for the current model.

Added formulas and explanation of hybrid retrieval system for RAG.

Docs #36

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** _see the commit that added this reproduction note (updated with the permalink in the following commit)_

**Reproduction summary:**
Because issue #36 is a documentation gap, "reproducing" it means confirming exactly what is missing and where. Running `grep -rni "bm25\|scoring\|formula\|weight\|normal" docs/` returns a single hit: `docs/ARCHITECTURE.md:60`, which describes the RAG retriever with one sentence — "Hybrid retrieval (vector similarity + BM25 keyword) fetches relevant context…" — and never states the scoring formula. Yet the code in `rag/retriever/` defines a very specific formula: vector scores come from `similarity = 1 / (1 + distance)` (`vector_store.py:103`), keyword scores are raw BM25Okapi scores (`keyword_search.py:45`), both are max-normalized to 0–1 (`hybrid.py:58-59, 70, 76`) and blended as `0.7·vector + 0.3·keyword` with a `min_score = 0.3` cutoff (`hybrid.py:14, 78-97`). None of that heuristic is documented, which is the gap the issue reports.

Reproduction steps:
1. `grep -rni "bm25\|scoring\|formula\|weight\|normal" docs/` → only `docs/ARCHITECTURE.md:60` mentions hybrid retrieval, with no formula.
2. Read `docs/ARCHITECTURE.md:59-60` (the "RAG System (`rag/`)" subsection) → one sentence, no scoring math, no default weights, no normalization or threshold.
3. Read `rag/retriever/hybrid.py`, `keyword_search.py`, `vector_store.py` → the actual weights (0.7 / 0.3), normalization, blend formula, and `min_score` threshold that a reader has no way to learn from the docs.

**PLAN.md link:** _added in the following commit — see `PLAN.md` at the repo root_

**Walkthrough video (recommended):** Not recorded (optional / not graded).

**Blockers or open questions:**
- `vector_store.py:37` creates the collection with `metadata={"hnsw:space": "cosine"}`, but `vector_store.py:102-103` comments that distances are "euclidean by default" before applying `1 / (1 + distance)`. I need to confirm in Week 9 which distance metric is actually in effect so the documented similarity formula is accurate.
- Whether to document the default `vector_weight` / `keyword_weight` (0.7 / 0.3) as fixed or configurable, since they are constructor arguments to `HybridRetriever`.

Docs #36