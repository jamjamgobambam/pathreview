## Solution plan

**Issue:** [#109 — Test coverage for core/services/review_service.py is below 40%](https://github.com/ascherj/pathreview/issues/109)

### Understand
<!-- What is the root cause of this issue? What behavior is expected vs. actual? -->

**Root cause of the testing gap:** No tests were written for `process_review` or its `_run_*` helpers. The fix is purely additive test code. `review_service.py` itself does not change.

**Expected vs. actual:** The pipeline is expected to end in one of three states — `complete` (all steps succeed), `failed` (a step fails cleanly, e.g. safety checks return `False` or the profile is missing), or `failed` via the outer `except` (an unexpected exception). None of these paths is currently exercised, so a regression in the critical review pipeline would pass CI silently.

### Map
<!-- Which files, functions, or modules are involved?
List the specific files you expect to touch. -->
These are the files, functions, and modules involved:

- **`core/services/review_service.py`:** the function under test (read-only reference) — `process_review()` and its helper functions `_run_ingestion_pipeline()`, `_run_agent_orchestration()`, `_run_rag_retrieval_generation()`, `_run_safety_checks()`.
- **`tests/unit/test_review_service.py`:** where I add the new tests, reusing the existing `mock_db_session()`, `mock_review()`, and `mock_profile()` fixtures (lines 19–45) and the `@pytest.mark.unit` / `@pytest.mark.asyncio` pattern already in the file.

**Note (pre-existing, out of scope):** 13 tests currently fail because `mock_db_session.execute`
returns an `AsyncMock`, so `result.scalars().first()` yields an un-awaited coroutine on
Python 3.14 (`RuntimeWarning: coroutine ... was never awaited`). My new tests stub
`execute` to return a plain `Mock()` result to avoid this trap. Since the existing
13 failures are out of scope, I will be leaving them for now unless a mentor asks.

### Plan
<!-- What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks. -->
1. **Baseline.** Run the coverage command above and check if the test coverage for `core/services/review_service.py` is below 40%. Record this "before" number.
2. **Helper unit tests (pure functions).** Test `_run_safety_checks()` directly: passes on well-formed output; returns `False` for no sections, an incomplete section (missing `content`/`section_name`), and out-of-range `confidence`. Test `_run_agent_orchestration()` / `_run_rag_retrieval_generation()` return dicts with the expected `sections`/`overall_score` keys. Test `_run_ingestion_pipeline()` builds sources for each of `github_username` / `portfolio_url` / `resume_text` and commits.
3. **`process_review()` success path.** Mock `db.execute` to return the review then the profile; patch the four `_run_*` helpers so safety checks pass; assert final `review.status == "complete"` and that `review.sections` / `overall_score` are set.
4. **`process_review()` clean-failure paths.** (a) profile not found -> `status == "failed"`; (b) `_run_safety_checks()` returns `False` -> `status == "failed"` and later helpers not reached; (c) review not found -> early `return`, no commit.
5. **`process_review()` unexpected-exception path.** Make a patched helper raise; assert the outer `except` sets `status == "failed"`, the error is logged, and no exception escapes.
6. **Re-run coverage.** Confirm the file is above 40%; record the "after" number.
7. **Edge case check.** Check for any hidden edge cases still not tested, with AI assistance.

### Inputs & outputs
<!-- What does your fix take as input? What should it produce or change? -->
**Functions under test** (signatures unchanged):
- `process_review(db, review_id: UUID, profile_id: UUID) -> None` — side-effect only:
  mutates `review.status` and commits; returns `None`.
- `_run_safety_checks(output: dict) -> bool`
- `_run_ingestion_pipeline(db, profile: Profile) -> list[dict]`

**Input to the tests:** a mocked async DB session and `Mock()` profile/review objects
(reusing existing fixtures).

**What the tests assert (define "done"):**
- Success: `review.status == "complete"`, `review.sections` populated, `db.commit` awaited.
- Clean failure: `review.status == "failed"`, downstream helpers not called.
- Exception: `review.status == "failed"`, no unhandled exception raised.

### Risks & unknowns
<!-- What could go wrong? What are you still unsure about? -->
1. **The `AsyncMock` vs `Mock` result trap.** `process_review` calls
   `result.scalars().first()` synchronously. A bare `AsyncMock` result turns
   `scalars()`/`first()` into coroutines and the assertion silently tests the wrong thing
   (this is why the 13 existing tests fail). I'll return a plain `Mock()` result and set
   `.scalars.return_value.first.return_value` explicitly.
2. **Multiple `execute` calls in one function.** `process_review` calls `execute` twice
   (review, then profile) and again inside the `except` block, so I need `side_effect` with
   an ordered list and enough entries for the failure path.
3. **`FeedbackSection` import (line 10).** The success path builds `FeedbackSection` and
   calls `.model_dump()`. Passing `{"sections": []}` avoids that branch; a test with a
   populated section must supply the keys `FeedbackSection` requires — I'll check
   `api/schemas/review.py` first.
4. **`datetime.utcnow()` (lines 171, 190).** Deprecated but harmless in tests; not patching
   unless it produces warnings that fail the suite.

### Edge cases
<!-- What inputs or states should your fix handle gracefully? -->
- Review not found (`execute` returns `None` first) → function logs and returns early, no commit.
- Profile not found → `status="failed"`, returns before running any helper.
- Safety checks fail (`_run_safety_checks` returns `False`) → `status="failed"`, sections never stored.
- Unexpected exception mid-pipeline → outer `except` sets `status="failed"`; if the
  status-update DB call *also* raises, the inner `except` swallows it (assert no exception escapes).
- Ingestion with a profile that has none of the three source fields → returns an empty list, still commits.
