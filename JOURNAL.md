## Week 7 – Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The architecture documentation says that hybrid retrieval combines vector and keyword search scores, but it does not explain the formula used to combine them. It also does not provide the default weights or an example calculation. A successful fix will add a clear section to `docs/ARCHITECTURE.md` explaining the scoring formula, the weights, and a simple example. This will help contributors understand how search results are ranked.

**Branch name:** docs/36-hybrid-retrieval-scoring

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger