## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

**Tier:** [x] Tier 1

**Problem summary:**
The relevance scorer test says it checks partial overlap, but its query matches every keyword in the text.
The scorer returns 1.0, so the assertion expects the wrong result.
The fixture should omit some query terms so the test checks partial overlap.
I chose this Tier 1 issue because it changes one test fixture and has a clear failing command.

**Branch name:** `test/157-partial-overlap-fixture`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
