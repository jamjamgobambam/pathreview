# Solution plan

**Issue:** [#158 — review_service unit tests misconfigure async mocks — 13 of 19 tests fail](https://github.com/ascherj/pathreview/issues/158)

## Understand

**Root cause.** `unittest.mock.AsyncMock` is contagious: every child attribute
auto-created on an `AsyncMock` is itself an `AsyncMock`, so calling it returns a
coroutine rather than a value. `tests/unit/test_review_service.py` builds the object
returned by `db.execute(...)` as `mock_result = AsyncMock()` (13 occurrences), which
makes `mock_result.scalars` an `AsyncMock` too. Configuring
`mock_result.scalars.return_value.first.return_value = mock_review` therefore sets up a
chain that is never reached — `result.scalars()` hands back an unawaited coroutine, and
the service's `.first()` / `.all()` call dies on it.

This misrepresents SQLAlchemy 2.x's actual async boundary. On an `AsyncSession`, only
`execute()` is awaitable; it returns an ordinary **synchronous** `Result`, whose
`.scalars()`, `.first()` and `.all()` are plain method calls. The correct mock shape
mirrors that split: `AsyncMock` for `execute`, a synchronous mock for the result.

**Expected vs. actual.**

| | Expected | Actual |
|---|---|---|
| `pytest tests/unit/test_review_service.py -q` | 19 passed | 13 failed, 6 passed |
| `result.scalars()` inside the service | `ScalarResult` mock | `<coroutine object AsyncMockMixin._execute_mock_call>` |
| Failure mode | — | `AttributeError: 'coroutine' object has no attribute 'first'` (and `'all'`), plus `RuntimeWarning: coroutine ... was never awaited` |

The 6 tests that pass are exactly the `create_review` ones — that path only touches
`db.add` / `db.commit` / `db.refresh` and never calls `execute`, so it never crosses the
broken boundary. Everything covering `get_review` and `list_reviews` fails, which means
the review CRUD paths currently have **no effective coverage**: a real regression in
ownership filtering or pagination would not be caught.

The service code in `core/services/review_service.py` is correct and must not change.

**A second, unreported defect.** I prototyped the mock-wiring fix in isolation before
writing this plan (swap `AsyncMock()` → `MagicMock()` for the result object) and got
**18 passed, 1 failed** — not the 19 the issue predicts. The straggler is
`test_list_reviews_ordered_by_created_at:340`, which asserts
`mock_db_session.execute.assert_called_once()`. But `list_reviews` legitimately calls
`execute` **twice** — once for the count query (`review_service.py:64`) and once for the
paginated query (`review_service.py:76`):

```
AssertionError: Expected 'execute' to have been called once. Called 2 times.
```

The broken async mocks were masking a wrong assertion. Fixing only what the issue
describes leaves the file red, so the fix has to cover both.

## Map

**Files I expect to touch:**

| File | Change |
|---|---|
| `tests/unit/test_review_service.py` | The entire fix. Mock wiring, the `assert_called_once` correction, and the tautological assertions. |
| `JOURNAL.md` | Week 8 entry (assignment deliverable, not part of the fix). |
| `PLAN.md` | This file. |

**Files I expect *not* to touch:**

- `core/services/review_service.py` — the service is correct; the issue says so
  explicitly and my reproduction confirms it. Changing it to accommodate a mock would be
  the wrong fix.
- `tests/conftest.py` — the shared fixtures there are text samples for the
  parser/scorer tests; nothing DB-related, and no other test file mocks a session
  (`grep -rln "scalars" tests/` returns only `test_review_service.py`). No shared
  fixture to update, and no precedent to follow — which means whatever shape I land on
  here becomes the reference for the next async-session test in this repo.

**Specific sites within `tests/unit/test_review_service.py`:**

- `mock_db_session` fixture — lines 19–27
- `mock_result = AsyncMock()` — 13 occurrences: lines 81, 98, 115, 132, 150, 201, 215,
  231, 261, 276, 291, 319, 333
- Wrong call-count assertion — line 340
- Tautological assertions — line 121 (`len(reviews) > 0 or len(reviews) == 0`),
  line 326 (`result is None or result is not None`)

## Plan

1. **Correct the async/sync boundary in the mock setup.** Replace each
   `mock_result = AsyncMock()` with a synchronous `MagicMock()`, keeping
   `db.execute` as an `AsyncMock` whose `return_value` is that result. Verified in a
   scratch prototype to take the file from 13 failures to 1.

2. **Extract the repeated setup into a helper.** The same four-line block is copy-pasted
   across 13 tests, which is how one wrong idea got replicated 13 times. Add a small
   fixture or module-level helper (e.g. `make_result(scalar_list)` returning a
   configured `MagicMock`) so the async boundary is expressed once, and have each test
   call it. This is the change that stops the bug recurring.

3. **Fix the `list_reviews` call-count assertion.** At line 340, replace
   `assert_called_once()` with an assertion matching real behaviour —
   `assert mock_db_session.execute.call_count == 2`, with a comment naming the two
   queries (count + paginated). Leave `get_review`'s `assert_called_once` alone; that one
   is genuinely a single call.

4. **Make `test_list_reviews_ordered_by_created_at` test its own name.** It currently
   asserts nothing about ordering. Inspect the `Select` object captured in
   `execute.call_args_list[1]` and assert the compiled statement carries
   `ORDER BY ... created_at DESC`, plus the `LIMIT`/`OFFSET` for the page. Same for
   `test_list_reviews_page_2_returns_correct_offset:141`, which captures `calls` and then
   only asserts `len(calls) > 0`.

5. **Replace the tautological assertions.** Lines 121 and 326 are true for every possible
   input and would stay green against arbitrarily broken code. Assert the real
   contract instead: that `reviews` is the list the mock returned and `total` equals its
   length; that `get_review` returns the mock review on a hit and `None` on a miss.

6. **Verify.** `pytest tests/unit/test_review_service.py -q` → 19 passed, no
   `RuntimeWarning: coroutine ... was never awaited`. Then `make check && make test-unit`
   per `docs/CONTRIBUTING.md` to confirm nothing else regressed.

## Inputs & outputs

**Input:** the existing test file and its 13 failing tests, run against unmodified
service code.

**Output:**
- `tests/unit/test_review_service.py` with mock fixtures that model
  `await execute()` → synchronous `Result` correctly.
- 19 passing tests that assert real behaviour — ownership filtering, pagination offsets,
  ordering, and the `(reviews, total)` contract — rather than passing vacuously.
- Zero unawaited-coroutine warnings in pytest output.
- No diff in `core/services/review_service.py`.

**Not in scope:** `process_review` and the `_run_*` helpers are untested in this file;
adding coverage for them is a separate issue, and widening scope here would make the PR
harder to review.

## Risks & unknowns

- **Fixing the symptom instead of the bug.** The failure mode is loud, so it's tempting
  to reach for `assert_called()` or drop assertions until the file goes green. That
  yields 19 passing tests worth nothing — the exact failure mode that produced lines 121
  and 326. Guardrail: after the fix, deliberately break `review_service.py` (invert the
  `Profile.user_id` filter at line 44, drop `.desc()` at line 72) and confirm tests go
  red. A test that doesn't fail on a real regression hasn't earned its place.
- **Scope creep into assertion quality.** Steps 4–5 go beyond the issue's literal ask.
  Step 3 is non-negotiable — without it the file can't reach 19 passed. Steps 4–5 are
  defensible as "the tests these were named for," but if a maintainer wants a minimal
  diff I'll split them into a follow-up issue rather than argue.
- **`MagicMock` vs `Mock` for the result.** `Mock` is likely sufficient, since nothing
  calls a dunder on the result. `MagicMock` is what I prototyped with and is the safer
  default against `len()` or iteration on a `ScalarResult`. Unknown worth 10 minutes:
  whether `Mock` passes too, and whether the repo's `ruff`/`mypy` config has an opinion.
- **`mock_reviews = [Mock(spec=['id', 'status'])]` at line 290.** Once these mocks are
  actually reached, `spec` starts being enforced — touching any other attribute raises.
  It currently passes only because the list is never returned. May need widening.
- **`make check` may already be failing** for unrelated reasons. `/health` is broken via
  known issues #154/#155, so a red baseline wouldn't necessarily be mine. I'll capture
  `make check` output on a clean `main` first so I can tell my breakage from
  pre-existing breakage.

## Edge cases

The fixed mocks must let the service handle, and the tests must actually cover:

- **Empty result set** — `scalars().all()` returns `[]`; `list_reviews` must return
  `([], 0)`, not raise or return `None`.
- **Ownership miss** — `scalars().first()` returns `None`; `get_review` returns `None`
  rather than raising. This is the security-relevant path: a review belonging to another
  user must not leak, so the "wrong user" test needs a real assertion.
- **Two executes, different shapes** — the count query and the paginated query hit the
  same mock. A single `return_value` gives both the same rows, so `total` and
  `len(reviews)` are always equal in tests. Real pagination has `total=57` with
  `len(reviews)=20`. Use `side_effect` with two distinct results so the count/page
  distinction is genuinely exercised — otherwise a fix that returns `len(reviews)` as
  `total` would pass.
- **Page beyond the end** — `page=99` on 5 reviews: offset exceeds the row count,
  `reviews` is empty but `total` still reports 5.
- **`page_size` boundaries** — the custom-size test uses 50; offset arithmetic
  `(page - 1) * page_size` at `review_service.py:60` should be asserted for page 1
  (offset 0) and page 2 (offset `page_size`).
