## Solution plan

**Issue:** [#158 — review_service unit tests misconfigure async mocks — 13 of 19 tests fail](https://github.com/ascherj/pathreview/issues/158)

### Understand

**Root cause.** The failing tests build the mocked query result as `mock_result = AsyncMock()`. On an `AsyncMock`, attribute access produces further async mocks, so `mock_result.scalars()` returns an **un-awaited coroutine** rather than a result-like object. The production code in `core/services/review_service.py` uses the real SQLAlchemy 2.x async pattern: it `await`s `db.execute(stmt)` and then calls the **synchronous** result API — `result.scalars().first()` (in `get_review`) and `result.scalars().all()` (in `list_reviews`). Calling `.first()` / `.all()` on a coroutine raises `AttributeError`.

**Expected vs. actual.**
- Expected: `pytest tests/unit/test_review_service.py -q` → 19 passed.
- Actual: 13 failed, 6 passed. Failures raise `AttributeError: 'coroutine' object has no attribute 'first'` (get_review tests) or `'...has no attribute 'all'` (list_reviews tests), originating at `review_service.py:47` and `:65`.

**Key insight:** the service code is correct and matches real async SQLAlchemy usage (`execute` is awaited; `scalars()`, `first()`, `all()` are synchronous). The bug lives entirely in the **test mock setup**, so no production code should change.

### Map

Files/functions involved:

- **`tests/unit/test_review_service.py`** — the only file to modify. The 13 affected tests each create `mock_result = AsyncMock()` and wire `mock_result.scalars.return_value.first/all.return_value`. Affected tests:
  - `test_get_review_returns_review_for_correct_owner`
  - `test_get_review_returns_none_for_wrong_user`
  - `test_get_review_uses_select_and_join`
  - `test_get_review_verifies_ownership`
  - `test_get_review_with_valid_uuid`
  - `test_list_reviews_returns_paginated_results`
  - `test_list_reviews_page_2_returns_correct_offset`
  - `test_list_reviews_returns_tuple`
  - `test_list_reviews_default_pagination`
  - `test_list_reviews_custom_page_size`
  - `test_list_reviews_counts_total`
  - `test_list_reviews_returns_reviews_list`
  - `test_list_reviews_ordered_by_created_at`
- **`core/services/review_service.py`** — read-only reference. `get_review` (line 47) and `list_reviews` (lines 65, 77). Confirm no change is needed here.

### Plan

1. **Make the result mock synchronous.** Replace `mock_result = AsyncMock()` with `mock_result = MagicMock()` in each affected test (add `MagicMock` to the `unittest.mock` import). Keep `mock_db_session.execute = AsyncMock(return_value=mock_result)` so `await db.execute(...)` still resolves to the sync result object. `mock_result.scalars().first()/.all()` then behave synchronously, matching the code.
2. **(Optional) De-duplicate.** Add a small helper (e.g. `make_execute_result(first=..., all_=...)`) or fixture that returns a `MagicMock` result with `.scalars().first()/.all()` pre-wired, and use it across tests so the same mistake can't be reintroduced.
3. **Verify the target file.** Run `pytest tests/unit/test_review_service.py -q` → expect **19 passed, 0 failed**.
4. **Check for regressions.** Run `make test-unit` to confirm nothing else depended on the old (broken) behavior.
5. **Lint + document.** Run `make check` (ruff/black/mypy) and update `JOURNAL.md` with the result.

### Inputs & outputs

- **Input:** the existing mock objects in `test_review_service.py`.
- **Output / change:** corrected test doubles so the mocked result exposes a synchronous `scalars().first()/.all()` chain. No production code changes.
- **Observable result:** `pytest tests/unit/test_review_service.py -q` reports 19 passed; overall unit suite stays green.

### Risks & unknowns

- Several tests only assert `mock_db_session.execute.assert_called_once()` and treat the result loosely — the switch to `MagicMock` must still satisfy those assertions (it should, since `execute` stays an `AsyncMock`).
- Need to confirm nothing in the suite relies on `scalars()` being awaitable; a repo-wide `grep "scalars"` in `tests/` before finalizing.
- If I introduce a shared helper/fixture (step 2), it must not alter the 6 `create_review` tests that already pass and don't use `scalars()`.
- Behavior depends on `unittest.mock` semantics under Python 3.13 (this environment) — verify the fix on the same interpreter the CI uses.

### Edge cases

- `.first()` returning `None` (wrong-owner and not-found paths).
- `.all()` returning an empty list **and** a populated list.
- `list_reviews` page 2: `list_reviews` calls `db.execute` **twice** (count query at line 64, page query at line 76). A single `return_value` is reused for both calls — confirm that still produces a valid `(reviews, total)` tuple.
- The count path does `len(count_result.scalars().all())`, so `.all()` must return a real Python list (a `MagicMock` list, or an explicit `[]`/list of mocks), not another mock, for `len()` to work.
