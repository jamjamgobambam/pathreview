## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/109

**Issue title:** Test coverage for core/services/review_service.py is below 40%

**Tier:** [ ] Tier 1 [x] Tier 2 [ ] Tier 3

**Problem summary:**
The tests in `tests/test_review_service.py` only cover 40% of codepaths. The review service provides core logic for the review lifecycle and CRUS/query functions, but the existing unit tests do not cover the processing pipeline. This fix will include comprehensive coverage of remaining unit tests to ensure intendend functionality of `core/services/review_service.py` when changes are made to it.

**Branch name:** `test/109-add-review-service-tests`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
