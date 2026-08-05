# Reproduction — Issue #158

**Issue:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail
**Link:** https://github.com/ascherj/pathreview/issues/158
**File under test:** `tests/unit/test_review_service.py`
**Code under test:** `core/services/review_service.py`

## How to reproduce

From the repository root, with the virtual environment active:

```bash
python -m pytest tests/unit/test_review_service.py -q
```

## Observed result

```
13 failed, 6 passed
AttributeError: 'coroutine' object has no attribute 'first'
AttributeError: 'coroutine' object has no attribute 'all'
```

The 13 failing tests are the ones that exercise `get_review` and
`list_reviews` (both read from the DB via `result.scalars()`), e.g.:

- test_get_review_returns_review_for_correct_owner
- test_get_review_returns_none_for_wrong_user
- test_list_reviews_returns_paginated_results
- test_list_reviews_page_2_returns_correct_offset
- test_list_reviews_returns_tuple
- test_get_review_uses_select_and_join
- test_list_reviews_default_pagination
- test_list_reviews_custom_page_size
- test_get_review_verifies_ownership
- test_list_reviews_counts_total
- test_list_reviews_returns_reviews_list
- test_get_review_with_valid_uuid
- test_list_reviews_ordered_by_created_at

The 6 tests that pass are the `create_review` tests, which never call
`result.scalars()` and therefore never hit the misconfigured mock.

## Root cause

In each failing test the result object is built as an `AsyncMock`:

```python
mock_result = AsyncMock()
mock_result.scalars.return_value.first.return_value = mock_review
mock_db_session.execute = AsyncMock(return_value=mock_result)
```

Because `mock_result` is an `AsyncMock`, its child attribute `scalars` is
also an `AsyncMock`, so **calling** `mock_result.scalars()` returns a
*coroutine* — not the configured `scalars.return_value`. The service code
in `review_service.py` awaits `db.execute(...)` (correct) and then calls
`result.scalars().first()` / `.all()` **synchronously**:

```python
result = await db.execute(stmt)
return result.scalars().first()          # get_review
...
total = len(count_result.scalars().all())  # list_reviews
```

So `.first()` / `.all()` are called on a coroutine → `AttributeError`.

The service logic is correct; only the test mocks are wrong.

## Verification of the fix direction (mock experiment)

`db.execute` must stay an `AsyncMock` (it is awaited), but the **result
object** must be a synchronous `MagicMock`, so that `scalars()`,
`first()`, and `all()` return configured values instead of coroutines:

```python
good = MagicMock()
good.scalars.return_value.first.return_value = "REVIEW"
good.scalars().first()   # -> "REVIEW"  (no AttributeError)
```
