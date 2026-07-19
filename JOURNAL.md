## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer "partial overlap" test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
There's a unit test, `test_query_with_partial_overlap`, that's supposed to check how the system scores a search query against a document chunk when they only partially match. Problem is, the test data doesn't actually represent a partial match. The query "Python Django web framework" and the chunk it's being compared to share all four words, so it's a 100% overlap, not partial. Because of that, the scorer correctly returns a perfect score of 1.0, but the test expects the score to be below 0.9, so it fails even though the scoring logic itself is working fine. The fix is just rewriting the fixture data so the chunk only shares some of the query's words, which will let the test actually verify partial-match behavior instead of accidentally testing full-match behavior. This is all in the `rag/` module, specifically the relevance scoring logic and its test file.

**Scope reasoning ("Is this issue right for me?"):**
I can explain the bug without going back to reread the issue: a test fixture that's supposed to represent partial overlap actually has full overlap, so the test fails even though the code itself is correct. It's a Tier 1 fix scoped to a single test file, which fits where I'm at as a first-time contributor to a large codebase. I already confirmed the relevant test file exists (`tests/unit/test_relevance_scorer.py`) and can be run directly with `pytest tests/unit/test_relevance_scorer.py -q` to reproduce the failure. There's an open PR (#164) already against this issue, so I know someone else is working it too, but since claims are non-exclusive I'm fine moving forward. I'm estimating this is a 1-2 hour fix once I'm actually in the code, which fits comfortably within the Week 8-9 timeline, and there don't seem to be any blockers or dependencies mentioned in the issue.

**Branch name:** fix/157-relevance-scorer-partial-overlap-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
(Note: the ledger spreadsheet isn't allowing edit access on my account, issue and claim are documented here and on GitHub instead.)