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

**Selection reasoning:**
I chose this issue because it's scoped to a single test file
(test_review_service.py) with a clearly reproducible failure command,
which fits my comfort level as a first-time contributor to a large
codebase. The fix only requires adjusting mock configuration (AsyncMock/
MagicMock), not touching the service logic itself, so the blast radius
is small and easy to verify by re-running pytest. This matches the
Tier 1 label — a good first issue that lets me practice the branch/PR
workflow without needing deep familiarity with the RAG or agent systems yet.

**Branch name:** fix/158-review-service-async-mocks

**Setup confirmation:** [x] App runs locally at localhost:5173
![alt text](image.png)

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tbnguye9/pathreview/commit/b41420d6413b53a4011b70427b5b1f4e5398861d

**Reproduction summary:**
Ran `python -m pytest tests/unit/test_review_service.py -q` in the local
venv and observed `13 failed, 6 passed` with `AttributeError: 'coroutine'
object has no attribute 'first'` / `'all'`. Confirmed the root cause: each
failing test builds the DB result object as an `AsyncMock`, so calling
`result.scalars()` returns a coroutine, and the service's synchronous
`.first()` / `.all()` call on that coroutine raises. The service logic is
correct — only the test mocks are misconfigured. Reproduction steps and a
mock experiment proving the fix direction are in
[docs/reproduction-158.md](docs/reproduction-158.md).

**PLAN.md link:** https://github.com/tbnguye9/pathreview/blob/fix/158-review-service-async-mocks/PLAN.md

**Walkthrough video (recommended):** _(not recorded yet — optional)_

**Blockers or open questions:**
Need to confirm CI's Python version matches my local 3.14 so `unittest.mock`
semantics are identical. Also deciding whether to hoist the repeated mock
setup into a shared fixture (cleaner, prevents regression) or keep the diff
minimal with an inline change per test — will pick based on maintainer
preference in Week 9.