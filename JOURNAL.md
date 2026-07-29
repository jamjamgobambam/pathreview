# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` currently says retrieval blends "vector similarity + BM25 keyword" search but never shows the actual math, so a reader can't tell how a chunk's final rank is produced or what happens if they want to retune it. Looking at the implementation in `rag/retriever/hybrid.py`, each chunk's vector and keyword scores are independently min-max normalized against the max score in that result set, then combined as `score = vector_weight * vector_score + keyword_weight * keyword_score` with defaults of 0.7/0.3, and anything below a 0.3 threshold is dropped before the top-`max_chunks` results are returned. None of that — the formula, the default weights, the normalization step, or the score-floor cutoff — is documented anywhere. A successful fix adds a section to `docs/ARCHITECTURE.md` that states the formula, the default weights, and walks through one worked example (e.g., a chunk with a raw vector score and BM25 score, normalized, blended, and compared against the 0.3 cutoff) so a new contributor can reason about retrieval ranking without reading the retriever source.

This is right for me because the issue mostly focus on RAG, retrieval scoring formula and architecture docs -- these focuses on design questions and issues, which could be reliable for me.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [commit not yet made — see below]

**Reproduction summary:**
Since this is a documentation gap rather than a runtime bug, "reproducing" it meant confirming the gap exists: `docs/ARCHITECTURE.md:60` states retrieval blends "vector similarity + BM25 keyword" with no formula, while `rag/retriever/hybrid.py` shows the actual blending is `score = 0.7 * norm(vector_score) + 0.3 * norm(keyword_score)` with per-side max-score normalization and a 0.3 blended-score cutoff — none of which appears in the doc. While tracing the formula I also found the vector-score conversion in `rag/retriever/vector_store.py` uses the Euclidean similarity formula (`1/(1+distance)`) on a collection configured for cosine distance, a discrepancy that needs a decision (document as-is vs. fix) before the new doc section is written.

**PLAN.md link:** https://github.com/nhatminh-07/pathreview/blob/docs/36-hybrid-retrieval-scoring-formula/PLAN.md (push the branch for this link to resolve)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
Need to decide whether fixing the cosine/Euclidean similarity discrepancy in `vector_store.py` is in scope for this PR, or whether to document current behavior as-is and file it as a separate follow-up issue.