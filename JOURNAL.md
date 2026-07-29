## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The partial-overlap unit test in `tests/unit/test_relevance_scorer.py` uses a query and chunk that share every query term. Because the relevance scorer measures query-token coverage, it correctly returns `1.0`, contradicting the test's expectation of a middle-range score. The fixture needs to omit some query terms while retaining others so it represents genuine partial overlap. A successful fix makes the test exercise the intended behavior without changing the correct scoring implementation.

**Branch name:** test/157-partial-overlap-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/xyin20/pathreview/commit/fac1dda72ac9ca4ab6a91ec808d66f7de0f73129

**Reproduction summary:**
I restored the original all-four-term fixture and ran the focused relevance scorer tests. The scorer correctly returned `1.0`, producing `assert 1.0 < 0.9` and a result of `1 failed, 18 passed`.

**PLAN.md link:** https://github.com/xyin20/pathreview/blob/test/157-partial-overlap-fixture/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
None.
