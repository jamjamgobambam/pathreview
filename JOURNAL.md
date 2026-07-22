# PathReview — Module 3 Journal

A running record of my Module 3 contribution work. A new section is added each week.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG system retrieves context by blending two signals — vector (semantic)
similarity and BM25 keyword relevance — but `docs/ARCHITECTURE.md` only mentions
that this blend happens without explaining how. Readers can't tell how the two
scores are combined, that each is min-max normalized to 0–1 before blending, or
that the defaults weight vector at 0.7 and keyword at 0.3. A successful fix adds
a section to the architecture doc that documents the scoring formula
(`blended = vector_weight * vector_score + keyword_weight * keyword_score`), the
normalization step, the default weights, and the `min_score` cutoff, illustrated
with a worked example. The behavior being documented lives in
`rag/retriever/hybrid.py` (`HybridRetriever`).

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
