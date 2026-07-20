## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `POST /reviews` API route is missing a test for the case where a profile exists but has no ingested documents. Without that coverage, the endpoint could crash or return an unclear error and nobody would catch it. A successful fix adds a unit test in `tests/unit/test_review_routes.py` that confirms the endpoint returns an appropriate error instead of failing unexpectedly.

**Branch name:** test/88-reviews-no-ingested-documents

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
