# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` currently states that hybrid retrieval blends vector
similarity and keyword scores, but it never shows the actual formula or the
default weighting between the two signals. A reader can't tell how much a
document's semantic match versus its keyword match contributes to its final
rank, or how to tune that balance. This affects the RAG/retrieval
documentation rather than the retrieval code itself. A successful fix adds a
clear section to `docs/ARCHITECTURE.md` that spells out the scoring formula,
states the default weights, and walks through a worked example so future
contributors can reason about (and safely adjust) retrieval ranking.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
