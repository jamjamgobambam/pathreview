# Module 3 Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88
**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, the codebase lacks a unit test to verify how the `POST /reviews` endpoint behaves when a user profile attempts to generate a review but has zero ingested documents. This gap in test coverage means potential edge-case failures or unhandled exceptions under empty document states might go unnoticed. A successful fix will involve writing mock test cases in the backend test suite to ensure the system gracefully handles empty-document profiles, returning the correct error code or empty response payload. This directly affects the backend routing and review service modules.

**Branch name:** test/88-review-endpoint-missing-documents
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger