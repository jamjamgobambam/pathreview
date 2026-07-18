## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/158](https://github.com/ascherj/pathreview/issues/158)

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The unit tests for the `review_service` currently fail because they incorrectly use `AsyncMock` for synchronous database result objects. Specifically, when the tests mock `db.execute()`, they return an `AsyncMock`. This raises an `AttributeError` in the service code. A successful fix will update the test setup in `tests/unit/test_review_service.py` to use a regular `Mock` or `MagicMock` for the query result object. This will correctly simulate the synchronous behavior of SQLAlchemy's query results, allowing all 19 tests to pass.

**Branch name:** [fix/158-review-service-async-mocks]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
