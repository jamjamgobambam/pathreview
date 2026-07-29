## Week 7 – Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The architecture documentation says that hybrid retrieval combines vector and keyword search scores, but it does not explain the formula used to combine them. It also does not provide the default weights or an example calculation. A successful fix will add a clear section to `docs/ARCHITECTURE.md` explaining the scoring formula, the weights, and a simple example. This will help contributors understand how search results are ranked.

**Branch name:** docs/36-hybrid-retrieval-scoring

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/ascherj/pathreview/commit/dfb3e54db650ace92c2b59103e4409572aad096a)

**Reproduction summary:**
I reviewed the RAG System section in `docs/ARCHITECTURE.md` and confirmed that it only states that vector similarity and BM25 keyword retrieval are combined. I then traced the implementation to `rag/hybrid.py`, where the scores are normalized and blended using default weights of 0.7 for vector similarity and 0.3 for BM25 relevance, none of which is currently documented.

**PLAN.md link:** (https://github.com/kennedypham108/pathreview/blob/docs/36-hybrid-retrieval-scoring/PLAN.md)

**Walkthrough video (recommended):** Not completed

**Blockers or open questions:**
I still need to verify the exact default scoring weights and score normalization behavior from the hybrid retrieval implementation.