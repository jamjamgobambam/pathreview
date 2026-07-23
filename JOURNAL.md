## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/109

**Issue title:** Test coverage for `core/services/review_service.py` is below 40%

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The review service orchestrates the full review workflow and is the most critical service in the application, but most of its code paths are untested. Add unit tests targeting the major execution paths including success, partial failure, and full failure cases.

Relevant files:

tests/unit/test_review_service.py



**Branch name:** test/109-test-coverage-service

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger