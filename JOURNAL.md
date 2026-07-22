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

**Cohort ledger:** [x] Issue added to cohort ledger
