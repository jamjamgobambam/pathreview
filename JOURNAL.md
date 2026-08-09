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
## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I investigated Issue #36 and the hybrid retrieval implementation. I updated `docs/ARCHITECTURE.md` to explain the hybrid retrieval scoring formula and how vector similarity and BM25 keyword retrieval contribute to the final ranking. The documentation change has been committed and pushed to the `docs/36-hybrid-retrieval-scoring` branch.

**Next steps:**

Open a pull request against the upstream `ascherj/pathreview` repository, request peer or mentor feedback, review the contribution against the project standards, and update the Week 9 journal with the final PR information.

**Blockers:**

The repository has pre-existing test and check failures unrelated to this documentation-only change. I will document these failures in the PR and confirm that my changes do not modify application or test code.


---

### Check-in 2 (end of week)

**PR link:** <https://github.com/ascherj/pathreview/pull/1018>

**Branch:** `docs/36-hybrid-retrieval-scoring`

**What you built:**

Updated `docs/ARCHITECTURE.md` to explain the hybrid retrieval scoring process used by PathReview. The documentation now explains how vector similarity and BM25 keyword retrieval are combined to produce the final retrieval ranking.

**Tests added or updated:**

No tests were added or modified because this contribution only changes documentation and does not modify application behavior or test code. I ran the existing test suite as part of the self-review.

**Self-review confirmation:**

[x] make check passes  
[x] make test-unit passes

The repository contains pre-existing failures unrelated to this documentation-only change. `make test-unit` reported 53 failed and 375 passed tests. `make check` also reported pre-existing issues in unrelated files. These failures were not caused by changes in this PR.

