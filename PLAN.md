## Solution plan

**Issue:** [review_service unit tests misconfigure async mocks — 13 of 19 tests fail](https://github.com/ascherj/pathreview/issues/158)

### Understand

**Root cause:** In `tests/unit/test_review_service.py`, tests for `get_review` and `list_reviews` build the SQLAlchemy query result as an `AsyncMock`. With `AsyncMock`, calling `.scalars()` returns a coroutine. The service code correctly treats the result as synchronous after `await db.execute(...)` and calls `.first()` / `.all()` without awaiting.

**Expected:** `pytest tests/unit/test_review_service.py -q` → all 19 tests pass. Mocks should mirror real async SQLAlchemy: `db.execute` is awaitable; the returned Result exposes sync `.scalars().first()` / `.all()`.

**Actual (reproduced locally):** 13 failed, 6 passed. Failures are:
- `AttributeError: 'coroutine' object has no attribute 'first'` on `get_review` tests
- `AttributeError: 'coroutine' object has no attribute 'all'` on `list_reviews` tests

The 6 passing tests are `create_review_*` cases that never call `.scalars().first()` / `.all()`.

**Important:** `core/services/review_service.py` is correct. This is a test-mock bug, not a production logic bug.

### Map

| Role | Path |
|---|---|
| Broken tests (will change) | `tests/unit/test_review_service.py` |
| Service under test (read-only; do not change) | `core/services/review_service.py` |
| Functions exercised | `get_review`, `list_reviews` (failing); `create_review` (already passing) |

Specific spots in the test file: every place that does `mock_result = AsyncMock()` and then wires `scalars().first()` / `scalars().all()`.

### Plan

1. **Confirm baseline** — Re-run `pytest tests/unit/test_review_service.py -q` and note 13 failed / 6 passed before changing anything.
2. **Fix the mock pattern** — Keep `session.execute` as `AsyncMock`. Change the returned result from `AsyncMock` to a sync `Mock` (or `MagicMock`) so `.scalars().first()` and `.scalars().all()` return normal values, not coroutines. Prefer a small helper/fixture so the pattern isn’t copy-pasted incorrectly again.
3. **Apply the fix across failing tests** — Update all `get_review` and `list_reviews` tests that currently use `mock_result = AsyncMock()`. Leave `create_review` tests alone unless a shared fixture change requires a touch-up.
4. **Account for `list_reviews` double `execute`** — `list_reviews` calls `db.execute` twice (count query + paginated query). Ensure mocks support both calls (e.g. same result shape for both, or `side_effect` if tests assert call counts).
5. **Verify** — Re-run `pytest tests/unit/test_review_service.py -q` (expect 19 passed) and optionally `make test-unit` / `make check` for the touched file.

### Inputs & outputs

**Inputs:**
- Existing unit tests in `tests/unit/test_review_service.py`
- Current (correct) async SQLAlchemy usage in `get_review` / `list_reviews`
- Local reproduction evidence: 13 failed / 6 passed

**Outputs / changes:**
- Updated mock setup in the test file only
- All 19 `test_review_service` tests passing
- No change to review CRUD behavior in production code
- No schema, API, or frontend changes

### Risks & unknowns

- **Over-fixing:** Accidentally changing `review_service.py` when the issue only asks for mock fixes.
- **Shared fixture side effects:** If the session fixture is made too aggressive, `create_review` tests could start failing.
- **Call-count assertions:** Some `list_reviews` tests may assume one `execute` call; the service makes two — a test may need a small assertion update after mocks work.
- **Style / lint:** Large mechanical edits might trip `ruff`/`black` on the test file; run format/lint on the touched file before opening a PR.
- **Unknown:** Whether graders expect a shared helper vs. inline `Mock` replacements — either is fine if tests pass and the pattern is clear.

### Edge cases

- **`get_review` returns a review** vs **returns `None`** — both must work with the sync result mock.
- **`list_reviews` empty list** vs **non-empty list** — `.all()` must return a real list so `len(...)` and tuple unpacking work.
- **Pagination args** (`page`, `page_size`) — mocks don’t need to implement SQL offset logic, but `execute` must still succeed for both internal queries.
- **Wrong-owner / missing review** — ownership filtering lives in the SQL statement; mocks should continue returning `None` when the test sets that up.
- **Warnings** — today’s `RuntimeWarning: coroutine ... was never awaited` should disappear once results are no longer `AsyncMock`s.
