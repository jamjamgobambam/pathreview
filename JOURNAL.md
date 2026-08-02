## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The architecture documentation mentions the hybrid retrieval system but does not explain how the retrieval score is calculated. This makes it difficult for new contributors to understand how keyword and semantic search results are combined and ranked. A successful fix would clearly document the hybrid retrieval scoring formula and explain how the different scoring components contribute to the final ranking.

**Branch name:** docs/36-hybrid-retrieval-scoring

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
https://github.com/navin-27/pathreview/commit/<commit-id>

**Reproduction summary:**

I reviewed `docs/ARCHITECTURE.md` and confirmed that it describes hybrid retrieval but does not explain how vector similarity and BM25 scores are combined to produce the final retrieval ranking. The documentation identifies the components but does not describe the scoring formula or ranking process.

**PLAN.md link:**
(https://github.com/navin-27/pathreview/blob/docs/36-hybrid-retrieval-scoring/PLAN.md

**Walkthrough video (recommended):**
Not recorded.

**Blockers or open questions:**

I need to identify where the hybrid retrieval scoring logic is implemented so the documentation accurately reflects the current behavior.