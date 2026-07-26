## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** `review_service unit tests misconfigure async mocks — 13 of 19 tests fail` 

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`review_service` unit tests are misconfigured to use Async mocks for the review `results` object, which leads to 13 tests out of 19 failing trying to call `.first()` on a coroutine (`AttributeError: 'coroutine' object has no attribute 'first'`). A successful fix would use `AsyncMock` for `execute` but use `MagicMock` for the review object, leading to a full passing suite.

**Selection reasoning:**

I chose this Tier 1 issue for several reasons including:

- This is my first time contributing to an open-source project (even if simulated).
- The fix is limited only to a unit test file `tests/unit/test_review_service.py` and doesn't need me to touch the actual review service itself, so I can get used to navigating the repo's test setup and conventions before tackling an issue that requires more knowledge of the codebase.
- I have little experience in pytest and I find it really interesting to understand the library and TDD in general.

**Branch name:** `fix/158-reviewservice-tests-fail`

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/rnossair/pathreview/commit/bdff0e3064fbac2d9f9b68533de7104cee48ff71

**Reproduction summary:**
I ran `pytest tests/unit/test_review_service.py -v` after `make setup` and saw 13 of 19 tests fail with `AttributeError: 'coroutine' object has no attribute 'first'` (or `'all'`), plus a `RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited` — confirming the `mock_result = AsyncMock()` mismatch described in the Week 7 problem summary.

**PLAN.md link:** [PLAN.md](https://github.com/rnossair/pathreview/blob/bdff0e3064fbac2d9f9b68533de7104cee48ff71/PLAN.md)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
No major blockers — root cause and fix are fully scoped in PLAN.md. Going into Week 9, the main thing I want to double check is whether any other test files in the repo have the same `AsyncMock`/`MagicMock` mismatch, so I can flag or fix those too rather than just this one file.