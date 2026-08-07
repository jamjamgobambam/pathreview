# Solution plan

**Issue:** [Test coverage for `core/services/review_service.py` is below 40% (#109)](https://github.com/ascherj/pathreview/issues/109)

### Understand

The stated behavior is that `review_service.py` — described as the most
critical service in the app — is under-tested. Reproduction showed the real
number is worse than stated: **22% coverage**, not ~40%. The existing 19 tests
in `tests/unit/test_review_service.py` only exercise `create_review`,
`get_review`, and `list_reviews`, and only their happy paths (13 of those 19
tests are additionally broken right now by an unrelated `AsyncMock`
misconfiguration bug tracked as issue #158 — see Risks below).

Expected behavior: the service's most important function, `process_review`
(the background task that runs ingestion → agent orchestration → RAG →
safety checks → sets the review's final status), should have its success
path, its two early-exit "partial failure" paths (missing profile, failed
safety check), and its outer exception handler ("full failure") all verified
by tests. Actual behavior: none of `process_review` is covered at all (lines
98-194 show 0% in the coverage report), nor is `_run_ingestion_pipeline`
(202-279, three independent try/except branches per source type) or
`_run_safety_checks` (369-390, three distinct rejection branches). This
matches the issue's framing exactly: the code paths that matter most
(success, partial failure, full failure) are the ones with zero coverage.

### Map

Files/functions this issue touches:

- `core/services/review_service.py` — the module under test, not expected to
  change (this is a test-only issue), specifically:
  - `process_review` (lines 98-194): success path, missing-profile branch,
    failed-safety-check branch, outer `except Exception` branch
  - `_run_ingestion_pipeline` (202-279): github/portfolio/resume ingestion,
    including each source type's individual `except Exception` branch
  - `_run_safety_checks` (369-390): no-sections / incomplete-section /
    invalid-confidence rejection branches, plus its own exception handler
  - `list_reviews` (lines 68-79 tail): the paginated-results query, only
    partially covered today
- `tests/unit/test_review_service.py` — where all new tests are added
- `core/models/review.py`, `core/models/profile.py`,
  `core/models/ingested_source.py` — read-only, to know what attributes to
  set on mock objects (`Review.status`, `Profile.github_username`, etc.)
- `api/schemas/review.py` (`FeedbackSection`) — read-only, to build fixture
  data matching the shape `process_review` expects from `rag_output`

### Plan

1. **Fix the mocking pattern before adding new tests.** The current
   `mock_db_session` fixture builds `db.execute` as a plain `AsyncMock`,
   which auto-mocks `.scalars()` on the return value as async too, breaking
   any code that calls a sync method on the result (`test/109` inherits this
   bug from #158). New tests will build the mocked `execute` return value
   explicitly (`Mock` with `.scalars.return_value.first/.all` set to plain
   values) instead of relying on `AsyncMock` autospec, so they don't fail the
   same way.
2. **Cover `process_review`'s success path** — mock `db.execute` to return a
   review and profile, stub `_run_ingestion_pipeline` /
   `_run_agent_orchestration` / `_run_rag_retrieval_generation` /
   `_run_safety_checks` to return canned data, assert the review ends with
   `status == "complete"`, `sections` populated, and `overall_score` set.
3. **Cover `process_review`'s partial-failure branches** — (a) profile not
   found → assert `status == "failed"` and early return; (b) safety checks
   return `False` → assert `status == "failed"` and early return, without the
   `sections`/`overall_score` fields being set.
4. **Cover `process_review`'s full-failure branch** — force
   `_run_agent_orchestration` (or another step) to raise, assert the outer
   `except` sets `status == "failed"`, and separately test the nested
   try/except (line 184-194) by making the recovery `db.execute` call itself
   raise, asserting it's caught and logged rather than propagating.
5. **Cover `_run_ingestion_pipeline` and `_run_safety_checks` directly** as
   unit tests (not just indirectly through `process_review`): each
   source-type branch (present/absent `github_username`, `portfolio_url`,
   `resume_text`) and each of the three safety-check rejection conditions.
6. **Re-run `pytest --cov` and confirm the module crosses well above 40%**
   (targeting the previously-zero-coverage functions should land in the
   70-85% range, since `_run_agent_orchestration`/`_run_rag_retrieval_generation`
   are static placeholder data with little branching left to cover).

### Inputs & outputs

- **Input:** no production code changes — only new/adjusted test functions in
  `tests/unit/test_review_service.py`, plus mocked `db`, `Profile`, and
  `Review` objects constructed per test.
- **Output:** a passing test suite for `review_service.py` with coverage
  measurably above 40% (verified via `pytest --cov=core.services.review_service
  --cov-report=term-missing`), and no test relying on the broken `AsyncMock`
  autospec pattern.

### Risks & unknowns

- **Issue #158 overlap:** 13 of the 19 *existing* tests in this exact file are
  already failing from the AsyncMock bug tracked in #158, which multiple
  other students have claimed. I'm not fixing those existing tests as part of
  #109 — only writing new tests that avoid the same trap — but if #158 lands
  first and changes the shared `mock_db_session` fixture, my new tests may
  need a rebase to stay consistent with whatever fixture pattern wins.
- **`process_review` has no dependency injection** for
  `_run_ingestion_pipeline` / `_run_agent_orchestration` /
  `_run_rag_retrieval_generation` / `_run_safety_checks` — they're called as
  module-level functions, not passed in. Testing `process_review` in
  isolation means `unittest.mock.patch`-ing these at the module path
  (`core.services.review_service._run_ingestion_pipeline`, etc.), which is
  more brittle than dependency injection would be. If patch targets are
  wrong (e.g. patching where it's defined instead of where it's imported)
  tests will silently not mock anything — need to verify each patch actually
  takes effect.
- **`datetime.utcnow()`** is called directly inside `process_review`
  (line 171, 190) rather than injected — tests asserting on `updated_at` will
  need to tolerate a real timestamp or patch `datetime` at the module level.
- Uncertain whether the course grader expects the coverage number to be
  captured in a specific format (e.g. a committed coverage report) beyond a
  passing `make test-unit` — will default to the `pytest --cov` invocation
  documented in `tests/unit/REPRODUCTION-109.md` unless told otherwise.

### Edge cases

- `create_review` / `get_review` / `list_reviews`: review ID that doesn't
  exist, review that exists but belongs to a different user's profile,
  `list_reviews` with `page_size` larger than total results, `page` beyond
  the last page (empty result, not an error).
- `process_review`: review row missing entirely (early return before any
  status change), profile row missing (sets `status="failed"` and returns),
  an ingested source with all three of `github_username`/`portfolio_url`/
  `resume_text` unset (should still complete without ingesting anything,
  not raise), one ingestion sub-step raising while the others succeed
  (should not abort the whole pipeline, per the existing per-branch
  try/except).
- `_run_safety_checks`: empty `sections` list, a section missing
  `section_name` or `content`, `confidence` outside `[0, 1]` (negative and
  `> 1`), and malformed input that raises inside the function itself
  (should be caught and return `False`, not propagate).
