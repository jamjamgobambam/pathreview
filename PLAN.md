## Solution plan

**Issue:** [#109 — Test coverage for `core/services/review_service.py` is below 40%](https://github.com/ascherj/pathreview/issues/109)

### Understand

**Expected behavior:** As the module that orchestrates the entire review workflow, `core/services/review_service.py` should have unit-test coverage well above the tier-2 bar (~80%), with the critical `process_review` pipeline exercising success, partial-failure, and full-failure paths.

**Actual behavior (reproduced locally):**
- Measured coverage is **22%** — even further below the 40% threshold the issue calls out.
- `process_review` (lines 82–194), `_run_ingestion_pipeline` (197–279), `_run_agent_orchestration` (282–304), `_run_rag_retrieval_generation` (307–354), and `_run_safety_checks` (357–390) have **zero** coverage.
- **13 of the 19 pre-existing tests fail** — the existing scaffolding uses `AsyncMock` where it needed `MagicMock` for the sync `result.scalars().first()` chain, producing `AttributeError: 'coroutine' object has no attribute 'all'`.
- Only the 6 `create_review` tests pass because they don't touch the `execute → scalars → first/all` chain.

**Root cause of the coverage gap:** The service was written before its tests. `create_review` got a partial suite; `process_review` and the four helpers were never tested. Compounding that, the tests that *do* exist for `get_review`/`list_reviews` are broken because their async-mocking pattern doesn't match how SQLAlchemy 2.0's `Result` object behaves (`scalars()` is sync).

### Map

**Files under test (no source changes planned):**
- `core/services/review_service.py` — 4 public async functions (`create_review`, `get_review`, `list_reviews`, `process_review`) + 4 module-level helpers (`_run_ingestion_pipeline`, `_run_agent_orchestration`, `_run_rag_retrieval_generation`, `_run_safety_checks`).

**Files I will touch:**
- `tests/unit/test_review_service.py` — repair 13 broken existing tests, add ~14 new tests targeting the uncovered lines.

**Files I will read but not edit (needed for accurate mocks):**
- `core/models/review.py`, `core/models/profile.py`, `core/models/ingested_source.py` — to know which attributes `process_review` reads/writes on mocked instances.
- `api/schemas/review.py` — `FeedbackSection` shape used inside `process_review`.
- `tests/conftest.py` — existing shared fixtures.

**Out of scope but noted:**
- `list_reviews` has a real bug on lines 63–65 — total count is computed as `len(count_result.scalars().all())` on the unpaginated query. Coverage tests will *surface* this; fixing it belongs in a separate issue.

### Plan

1. **Fix the broken existing mocks (unblocks measurement).** Replace `AsyncMock` with `MagicMock` for `result.scalars()` in every existing test. `db.execute` stays `AsyncMock`; `.scalars()` and `.first()`/`.all()` become sync. This alone should turn 13 red tests green and raise coverage into the 30s.

2. **Add shared test helpers.** Inside `TestReviewService`, add:
   - `_exec_result(value)` — builds a sync `MagicMock` whose `.scalars().first()` returns `value`.
   - `mock_profile_full` fixture — profile with `github_username`, `portfolio_url`, `resume_text`, `resume_filename` set (drives happy path).
   - `mock_profile_empty` fixture — profile with all source fields `None` (drives no-source case).
   These prevent copy-paste drift across the ~14 new tests.

3. **Cover `process_review` — 8 tests, one per branch of [review_service.py:82-194](core/services/review_service.py#L82-L194).** Full-pipeline success; review-not-found early return; profile-not-found → `status=failed`; safety-check-fail → `status=failed`; partial ingestion failure (one source raises, others succeed); unexpected exception mid-pipeline → outer handler flips status; exception + recovery-write also fails → no crash propagated; profile with only one source. Each patches the four internal helpers with `patch.object(review_service, "_run_...")` so tests aren't coupled to the placeholder return values.

4. **Cover the helpers directly — 6 tests.** `_run_ingestion_pipeline`: all-sources-present and no-sources-present. `_run_safety_checks`: valid output (True), missing sections (False), invalid confidence range (False), missing section_name/content (False). `_run_agent_orchestration` and `_run_rag_retrieval_generation` are placeholder stubs — one shape-assertion each is sufficient for coverage bookkeeping.

5. **Verify and lock in.** Run `.venv/bin/pytest tests/unit/test_review_service.py --cov=core.services.review_service --cov-report=term-missing`. Target ≥ 80% coverage with only trivial log-line uncovered. Then `make check` (ruff + black + mypy — tests are excluded from mypy per Makefile:57, but ruff still runs on them).

### Inputs & outputs

**Inputs (what the fix operates on):**
- The existing 340-line `tests/unit/test_review_service.py`.
- The uncovered code paths in `core/services/review_service.py` (identified by line ranges 68–79, 98–194, 202–279, 288, 323, 369–390 from the coverage report).

**Outputs (what the fix produces):**
- Repaired existing tests (13 currently failing → passing).
- ~14 new test cases named for the branch they cover.
- Measured coverage on `core/services/review_service.py` at ≥ 80% (from 22%).
- No changes to production source code.
- No new files.

### Risks & unknowns

- **Sequenced-mock fragility.** `process_review` calls `db.execute(...).scalars().first()` up to three times (review lookup at :101, profile lookup at :110, exception-handler re-fetch at :186). Tests use `AsyncMock(side_effect=[...])` on `db.execute` with sync `MagicMock` wrappers per call. If the source function's call order changes, every affected test breaks with a confusing "wrong value returned" error, not a clean failure. Mitigation: keep the `_exec_result` helper inline in each test and comment which call each sequence entry represents.

- **Async vs sync mock split is easy to get wrong.** Symptom: `'coroutine' object has no attribute 'X'` (the exact error the existing broken tests throw). Rule: `db.execute` = `AsyncMock`; everything after (`.scalars()`, `.first()`, `.all()`) = `MagicMock`; `db.add` = plain `Mock` (sync). Will document at the top of the test file.

- **Placeholder helpers may get real implementations before this PR merges.** `_run_agent_orchestration` etc. currently return hardcoded stubs. If someone lands a real implementation first, my `patch.object` targets still work (patching by module attribute), but the direct helper tests (step 4) will need updated fixtures. Low probability given the branch state, worth watching in review.

- **The `list_reviews` count bug.** My tests will exercise the buggy branch and pass (because `.scalars().all()` mocked to return a small list) — meaning I'll be *codifying* the bug into a test. Mitigation: add a `# TODO(#TBD)` comment referencing a follow-up issue rather than pretending it's correct behavior.

- **Unknown: exact coverage number I'll land at.** The 5 log-statement lines in exception blocks are hard to hit without contrived mocks. 80% is a target, not a guarantee — may land at 78–82%. If below 80%, I'll add one more `process_review` variant to cover a nested log branch.

### Edge cases

- Profile with **no** ingestible sources (`github_username`, `portfolio_url`, `resume_text` all `None`) — `_run_ingestion_pipeline` should return `[]` and still `commit()`.
- Profile with **only one** source — pipeline runs, that source's `IngestedSource` row is added, other branches skipped.
- **Empty `sections` list** returned by RAG output — `_run_safety_checks` must return `False` and status must become `failed` (line 371–373).
- **Confidence out of range** — a section with `confidence=1.5` or `confidence=-0.1` must fail safety.
- **Section missing `section_name` or `content`** — must fail safety.
- **Exception raised** by one of the ingestion sources (e.g., GitHub API failure) — the per-source try/except must swallow it, log it, and still let the review complete via the remaining sources.
- **Exception raised** by a whole pipeline step (agent/RAG/safety) — the outer try/except must flip `review.status = "failed"` and commit.
- **Exception raised again inside the exception handler** (nested at :193–194) — must be swallowed and logged, no propagation.
- **`review_id` valid but review record deleted mid-processing** — the re-fetch at :186 returns `None` and the recovery block does nothing.
- **`user_id`-mismatched review in `get_review`** — the join filter must return `None`, not the row.
- **Empty result set** for `list_reviews` — returns `([], 0)`, not an error.
- **`page=2` with fewer than `page_size` results** — offset math still produces a valid query; the returned list is empty but `total` reflects the true row count.
