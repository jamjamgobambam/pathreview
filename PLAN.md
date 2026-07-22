# Solution plan

**Issue:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail — https://github.com/ascherj/pathreview/issues/158

### Understand

**Root cause.** In `tests/unit/test_review_service.py`, every test that
exercises a read path builds the SQLAlchemy result object as an
`AsyncMock`:

```python
mock_result = AsyncMock()
mock_result.scalars.return_value.first.return_value = mock_review
mock_db_session.execute = AsyncMock(return_value=mock_result)
```

Because `mock_result` is an `AsyncMock`, its `scalars` attribute is also
an `AsyncMock`, so **calling** `mock_result.scalars()` returns a
*coroutine* rather than the configured `scalars.return_value`. The
production code in `core/services/review_service.py` correctly awaits
`db.execute(...)` and then calls `.scalars().first()` / `.scalars().all()`
**synchronously** on the result. Calling `.first()` / `.all()` on a
coroutine raises `AttributeError: 'coroutine' object has no attribute ...`.

**Expected vs. actual.**
- Expected: `pytest tests/unit/test_review_service.py` → 19 passed.
- Actual: 13 failed, 6 passed. The 6 that pass are the `create_review`
  tests, which never call `result.scalars()`.

The service logic is correct. Only the test mock configuration is wrong,
so this is a test-only fix.

### Map

Files involved:

- **`tests/unit/test_review_service.py`** — the only file I expect to
  change. The `mock_result = AsyncMock()` lines (13 occurrences across the
  failing tests) must become synchronous mocks.
- **`core/services/review_service.py`** — read-only reference. Confirms
  the awaited-vs-synchronous call pattern (`await db.execute(...)` then
  `result.scalars().first()` / `.all()`); no change needed.
- **`docs/reproduction-158.md`** — reproduction notes I added (evidence).

### Plan

1. **Replace the result-object mock type.** In each failing test change
   `mock_result = AsyncMock()` → `mock_result = MagicMock()` (add
   `MagicMock` to the `unittest.mock` import). Leave
   `mock_db_session.execute = AsyncMock(return_value=mock_result)` alone —
   `execute` is awaited and must stay async.
2. **Optionally hoist a shared helper/fixture.** Add a small fixture (e.g.
   `mock_result_with_first` / `mock_result_with_all`) so the mock is
   configured in one place instead of repeated in 13 tests, reducing the
   chance the bug reappears.
3. **Re-run the target file** with `pytest tests/unit/test_review_service.py -q`
   and confirm 19 passed, 0 failed, and no "coroutine was never awaited"
   warnings.
4. **Run the wider unit suite** (`pytest tests/unit -q`) to confirm no
   regressions elsewhere, and run the linters/pre-commit hooks the repo
   configures.
5. **Open the PR** against `ascherj/pathreview`, referencing issue #158,
   with the before/after pytest output in the description.

### Inputs & outputs

- **Input:** the existing failing tests and the unchanged service code.
- **Output:** the same tests, with the result object mocked as a
  synchronous `MagicMock` whose `scalars().first()` / `scalars().all()`
  return the configured values. No production code changes.
- **Observable change:** `pytest tests/unit/test_review_service.py` goes
  from `13 failed, 6 passed` to `19 passed`.

### Risks & unknowns

- **`AsyncMock` vs `MagicMock` boundary.** The one thing that must stay
  async is `db.execute`; if I accidentally make it synchronous, the
  `await db.execute(...)` in the service will fail. I'll keep `execute` as
  `AsyncMock` and only change the result object.
- **`create_review` tests are already green** — I must not break them. My
  change only touches the `get_review` / `list_reviews` tests, so they
  should be unaffected, but I'll verify with a full run.
- **Assertion strength.** Some tests only assert `isinstance(..., int)` /
  "no exception". Once the mocks work, I should check whether any test now
  needs a stronger assertion (e.g. `list_reviews` returning the mocked
  reviews) — but tightening assertions is out of scope unless the
  maintainer asks, to keep the diff minimal.
- **Python 3.14 mock behavior.** I'm on Python 3.14; I'll confirm CI's
  Python version matches so mock semantics are the same there.

### Edge cases

- Tests using `scalars().first()` returning **`None`** (wrong-owner path)
  must still work with `MagicMock` — `first.return_value = None`.
- Tests using `scalars().all()` returning an **empty list** (pagination
  page 2, default pagination) — `all.return_value = []`.
- Tests using `scalars().all()` returning a **populated list** (5 reviews)
  — the count-then-page path in `list_reviews` calls `execute` twice, so
  the mock must serve `scalars().all()` correctly on repeated calls.
- No "coroutine was never awaited" `RuntimeWarning` should remain after
  the fix — its absence is part of the acceptance check.
