## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The unit tests in test_review_service.py fail because the async
database mock is set up incorrectly. The service code properly awaits
db.execute(...) and then calls .scalars().first() or .scalars().all()
on the result, but the test mocks make execute() itself return a plain
coroutine instead of a mock result object, so scalars() is called on a
coroutine rather than a proper mock — causing an AttributeError. The
service logic in review_service is actually correct; only the test
mocks need to be reworked (e.g. using AsyncMock for execute() and a
MagicMock for the returned result object) so that 13 currently-failing
tests pass.

**Branch name:** fix/158-review-service-async-mocks

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger