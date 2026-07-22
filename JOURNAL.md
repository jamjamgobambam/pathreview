## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks - 13 of 19 tests fail

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The failing unit tests in the review service are mostly caused by incorrect async mock wiring, not by broken service logic. In the current setup, db.execute(...) is awaited correctly in service code, but the tests return a coroutine from result.scalars(), which then crashes when first() or all() is called. This leads to AttributeError failures that mask whether CRUD behavior is actually correct. A successful fix will reconfigure the test mocks so execute is async while the query result chain behaves like synchronous SQLAlchemy result objects. This affects tests in tests/unit/test_review_service.py and should make the existing review_service CRUD tests meaningful.

**Branch name:** fix/158-review-service-async-mock-tests

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
