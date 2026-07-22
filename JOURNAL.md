## Week 7 — Issue selection


**Issue link:** https://github.com/ascherj/pathreview/issues/88


**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents


**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3


**Problem summary:**
From reading the issue, it looks like `POST /reviews` is missing a test for the scenario where a profile exists but no resume or repositories have been ingested yet. Since the review generator wouldn't have any data to work with, I'll verify how the endpoint currently handles that situation and add a test in `tests/unit/test_review_routes.py` to ensure it returns an appropriate error rather than crashing.


**Branch name:** test/88-review-endpoint-no-ingested-content


**Setup confirmation:** [x] App runs locally at localhost:5173


**Cohort ledger:** [x] Issue added to cohort ledger
