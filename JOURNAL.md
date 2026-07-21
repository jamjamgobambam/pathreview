## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/109

**Issue title:** Test coverage for core/services/review_service.py is below 40%

**Tier:** [x] Tier 2  [ ] Tier 1  [ ] Tier 3

**Problem summary:**
The `review_service.py` module orchestrates the entire review pipeline — fetching
a user's profile, running ingestion (GitHub, portfolio, resume), agent analysis,
RAG generation, and safety checks — but most of this logic currently has no unit
tests. This matters because `process_review` has several distinct outcomes (full
success, a missing profile, a failed safety check, and an unhandled exception
mid-pipeline) that each set the review's status differently, and none of that
branching logic is currently verified. A successful fix adds unit tests in
tests/unit/test_review_service.py that exercise each of these paths so future
changes to the pipeline don't silently break review processing.

**Branch name:** test/109-review-service-coverage

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger