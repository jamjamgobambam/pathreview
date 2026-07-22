## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The partial-overlap unit test in `tests/unit/test_relevance_scorer.py` uses a query and chunk that share every query term. Because the relevance scorer measures query-token coverage, it correctly returns `1.0`, contradicting the test's expectation of a middle-range score. The fixture needs to omit some query terms while retaining others so it represents genuine partial overlap. A successful fix makes the test exercise the intended behavior without changing the correct scoring implementation.

**Branch name:** test/157-partial-overlap-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
