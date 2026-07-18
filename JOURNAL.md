## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Selection reasoning:**
I selected this Tier 1 issue because I am comfortable writing focused unit tests but am still becoming familiar with the project's review API and error-handling flow. The change has a narrow scope in one test file, making it a manageable way to learn how the endpoint handles profiles and ingested content.

**Problem summary:**
The unit tests for the review routes do not cover the case where a valid profile exists but has no associated ingested content. As a result, a regression could cause the `POST /reviews` endpoint to crash instead of returning a controlled error response. The missing coverage belongs in `tests/unit/test_review_routes.py` and should exercise this empty-content condition. A successful change will verify that the endpoint responds with an appropriate error status and message when there is nothing available to review.

**Branch name:** `tests/88-POST-/reviews-endpoint-has-no-test-for-when-the-profile-has-no-ingested-documents-`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
