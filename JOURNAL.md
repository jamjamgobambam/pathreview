## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36
**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `docs/ARCHITECTURE.md` file currently describes that the RAG subsystem performs hybrid retrieval by blending vector similarity and keyword search results, but it does not specify how this blending is calculated. Specifically, it lacks details on the mathematical formula used to combine the scores, the default weights applied to each search method, and how the scores are normalized. A successful fix will add a detailed section to `docs/ARCHITECTURE.md` explaining this scoring process, detailing the default weights of 0.7 for vector and 0.3 for keyword searches, and providing a step-by-step example of how the blended score is computed for a document chunk.

**Branch name:** docs/36-explain-hybrid-retrieval-scoring

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
