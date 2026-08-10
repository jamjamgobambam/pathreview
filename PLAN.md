## Solution plan

**Issue:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail:  https://github.com/ascherj/pathreview/issues/158

### Understand

In each failing test, `mock_result` is created as `AsyncMock()`. Because `AsyncMock` makes every attribute access return a coroutine, calling `mock_result.scalars()` returns a coroutine instead of a plain object. The service code then calls `.first()` or `.all()` on that coroutine, which raises `AttributeError` since coroutines have no such methods.

### Map

The file I need to touch is the test_review_service file, because its where the module for
testing the review_service file is. In the test file I will touch all the functions that call
mock_db_session.execute — specifically the 13 tests where `mock_result = AsyncMock()` is used.

File: `tests/unit/test_review_service.py`

Functions to update:

- test_get_review_returns_review_for_correct_owner (line 81)
- test_get_review_returns_none_for_wrong_user (line 98)
- test_list_reviews_returns_paginated_results (line 115)
- test_list_reviews_page_2_returns_correct_offset (line 132)
- test_list_reviews_returns_tuple (line 150)
- test_get_review_uses_select_and_join (line 201)
- test_list_reviews_default_pagination (line 215)
- test_list_reviews_custom_page_size (line 231)
- test_get_review_verifies_ownership (line 261)
- test_list_reviews_counts_total (line 276)
- test_list_reviews_returns_reviews_list (line 291)
- test_get_review_with_valid_uuid (line 319)
- test_list_reviews_ordered_by_created_at (line 334)

No changes needed to `core/services/review_service.py`.

### Plan

What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. **Reproduce the bug** — Run `pytest tests/unit/test_review_service.py -q` and confirm 13
   tests fail with `AttributeError: 'coroutine' object has no attribute 'first'` or `'all'`.
2. **Fix the mock setup** — In each of the 13 failing tests, change:

   ```python
   mock_result = AsyncMock()
   ```

   to:

   ```python
   mock_result = Mock()
   ```

   Leave `mock_db_session.execute = AsyncMock(return_value=mock_result)` unchanged —
   `execute` must remain async because the service awaits it.
3. **Verify the fix** — Run `pytest tests/unit/test_review_service.py -q` again and confirm
   all 19 tests pass.
4. **Commit and push** — Stage the changed test file, commit with a descriptive message,
   and push to the working branch.

### Inputs & outputs

What does your fix take as input? What should it produce or change?

**Input:** The broken test file `tests/unit/test_review_service.py` where `mock_result` is
incorrectly typed as `AsyncMock()`.

**Output / change:** The same test file with `mock_result = Mock()` in all 13 affected tests.
The service code is untouched. Running the test suite should go from 13 failed / 6 passed
to 0 failed / 19 passed.

### Risks & unknowns

What could go wrong? What are you still unsure about?

- **Other tests breaking:** The 6 tests that currently pass (the `create_review` tests) do
  not use `mock_result`, so they will not be affected.
- **AsyncMock side effects:** Changing `mock_result` to `Mock` only affects the result object.
  All async session methods (`execute`, `commit`, `refresh`) remain as `AsyncMock` and will
  still behave correctly.
- **No risk to service code:** The fix is entirely in the test file, so production behaviour
  is unchanged.

### Edge cases

What inputs or states should your fix handle gracefully?

- `get_review` returning `None` — already tested in `test_get_review_returns_none_for_wrong_user`;
  the fix does not change that assertion, it just makes the mock chain work correctly.
- Empty list from `list_reviews` — several tests pass `[]` as the return value of `.all()`;
  these should still work correctly after the fix since `Mock` supports the same chaining.
- Multiple `execute` calls in `list_reviews` — the function calls `db.execute` twice (once
  for count, once for paginated results). Both calls return the same `mock_result`, which is
  fine since the tests only check that results are the correct type, not specific values.
