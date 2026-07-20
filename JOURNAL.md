## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/109

**Issue title:** Test coverage for core/services/review_service.py is below 40%

**Tier:** [ ] Tier 1 [x] Tier 2 [ ] Tier 3

**Problem summary:**
The tests in `tests/test_review_service.py` only cover 40% of codepaths. The review service provides core logic for the review lifecycle and CRUD/query functions, but the existing unit tests do not cover the processing pipeline. This fix will include comprehensive coverage of remaining unit tests to ensure intended functionality of `core/services/review_service.py` when changes are made to it.

**Reasoning (from checklist):**
Part 1: I can explain the problem and expected behavior (above). The issue is related to tests for `review_service.py` which holds the business logic and functionality of the review API and also touches on ingestion. The tests currently cover <40% of codepaths and must be updated to include more comprehensive testing so that changes made to `review_service.py` can be tested to ensure intended functionality. "Done" would look like a complete list of tests that address the major execution paths including success, partial failure and full failure cases.

Part 2: I have contributed to large codebases before, so I've chosen a Tier 2 issue.

Part 3: I've found and read the specific code the issue references (`tests/unit/test_review_service.py`), and understand that the tests currently cover `create_review`, `get_review` and `list_review`, but do not cover `process_review`. I've read enough surrounding context that I can write a rough plan. The test file is the one I am changing and I've read at least one test end-to-end (`test_create_review_reurns_review_with_pending_status`).

Part 4: No one else has commented claiming this issue (at time of selection, cohort ledger does not yet exist or has not been provided). I've estimated this will wake me about 6 hours and I am confident I can complete it before the week 9 deadline. This issue has no open blockers or dependencies.

**Branch name:** `test/109-add-review-service-tests`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**AI Usage:** I used Claude to review the `review_service.py` and `test_review_service.py` to give me a rundown of the exisiting functions, why they are used and to highlight cases where unit tests are missing.

<hr>

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jdingeman/pathreview/commit/abcb666babe288113e36092ebb7c4a7d4e504af1

**Reproduction summary:**
I isolated the tests by running `pytest tests/unit/test_review_service.py > temp_test_review_service_output.txt 2>&1` so I could see the test results. I found that several of the existings tests are failing due to syntax issues, though it is outside the scope of this fix. The tests only cover `create_review`, `get_review` and `list_reviews` but not `process_review`

**PLAN.md link:** PLAN.md

**Walkthrough video (recommended):** _Covered by temp_test_review_service_output.txt_

**Blockers or open questions:**
I am unsure about the setup of the existing tests and if my tests should be implemented the same way since the exisitng ones fail due to syntax. See temp_test_review_service_output.txt
