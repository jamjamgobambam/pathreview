## Week 7: Issue Selection

**Issue link:** https://github.com/ascherj/pathreview/issues/6

**Issue title:** Duplicate embeddings generated when re-ingesting the same repository

**Tier:** [x] Tier 2
Touches both ingestion pipeline and database model layer, rather than simply one file. The estimated duration for the issue is 4-6 hours, which falls within the window of Weeks 7-9. I'd worked with SQLAlchemy models previously, so a cross-module problem seemed manageable.

**Problem summary:**
When you submit the same repository twice, PathReview doesn't recognize that it has previously been completed; instead, it repeats the whole embedding process. There is a safeguard for this: the 'IngestedSource' has an indexed 'content_hash' column. But it's broken in two places. Skip check never executes because `_check_skip()` in `ingestion/pipeline.py` accesses the database incorrectly and fails quietly, captured by a broad try/except. And even if the query was successful, there would be nothing to verify against because `_record_ingested_source()` merely records a message and never stores a row. As a result, each re-ingestion accumulates duplicate embeddings, skewing retrieval in favor of the duplicate. Fix: Make ingestion idempotent. Check the content hash, disregard everything that has already been consumed, still process what's new or changed.

**Branch name:** `fix/6-duplicate-embeddings-reingest`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jl17500/pathreview/commit/3c400a53c9061d235847a6983e59e74c171c2b51

**Reproduction summary:**
Created a test that runs `ingest_resume()` twice with the same content after instantiating the real `IngestionPipeline` with a `db_session` mock spec'd to `AsyncSession` (the actual session type used in `core/database.py`). Because `AsyncSession` lacks a `.query()` function, it verifies that `_check_skip()` raises `AttributeError: 'Mock' object has no attribute 'query'`; the error is silently consumed, and `batch_processor.process` runs twice rather than once for identical input.

**PLAN.md link:** https://github.com/jl17500/pathreview/blob/fix/6-duplicate-embeddings-reingest/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
While mapping call sites, discovered a second unrelated error in 'core/services/review_service.py': '_run_ingestion_pipeline()' creates 'IngestedSource(..., raw_data=...)' with a kwarg that the model lacks, which is quietly swallowed by a broad unless. It's on a live path ('POST /reviews'), but it's not relevant to problem #6, which only focuses on the pipeline and model layer. Flagging it for a possible follow-up issue rather than fixing it now.


---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the full fix from PLAN.md: rewrote `_check_skip()` to use a real
async SQLAlchemy query (`select()` + `await db_session.execute()`) filtered
on `profile_id`, `content_hash`, and `source_type`, instead of the broken
sync `.query()` call that silently failed and always returned None.
Rewrote `_record_ingested_source()` to actually persist an `IngestedSource`
row (previously it only logged). Converted `ingest_resume`, `ingest_readme`,
and `ingest_repo_metadata` to async to support both changes. Updated the
Week 8 reproduction test to await the new async methods; it now passes.
Added a new test file, `tests/unit/test_pipeline.py`, with 5 tests covering
the dedup logic from both the helper level and the full `ingest_resume` flow.
Ran the full `tests/unit` suite before and after the fix and confirmed the
same 53 pre-existing failures remain unchanged (54 minus the one this PR
fixes), with no new failures introduced.

**Next steps:**
Open a draft PR and request review from a classmate or mentor in Slack.
Finalize the PR description (issue link, manual verification steps,
pre-existing-failure documentation) and submit by Sunday.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/867

**Branch:** `fix/6-duplicate-embeddings-reingest`

**What you built:**
Fixed duplicate embeddings on repository re-ingestion (issue #6). Two stacked bugs in `ingestion/pipeline.py`: `_check_skip()` called the old sync SQLAlchemy `.query()` API on an `AsyncSession` (which has no such method), so the resulting error was silently swallowed and the function always returned "proceed"; separately, `_record_ingested_source()` never wrote anything to the database. Rewrote both to use the real async ORM API, and converted the three `ingest_*` entry points to `async def` accordingly.

**Tests added or updated:**
Updated `tests/unit/test_pipeline_repro.py` (Week 8 reproduction test) to await the now-async methods and mock `db_session.execute()` instead of `.query()`, it now passes. Added `tests/unit/test_pipeline.py` with 5 new tests: `_check_skip` returns None/skip-result correctly in isolation, `_record_ingested_source` actually persists a row with correct fields, `ingest_resume` doesn't incorrectly skip when content changes between calls, and `ingest_resume` proceeds normally for a profile with no prior ingestions.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both pass in the sense the assignment defines for a codebase with documented pre-existing failures: my changes introduce zero new failures. Full suite before my fix: 54 failed/375 passed; after: 53 failed/381 passed. The only change is the repro test flipping from fail to pass, plus 5 new passing tests. mypy shows the same 12 pre-existing, unrelated type errors before and after. Full detail in the PR's "Notes for Reviewers.")

**Draft PR feedback received from:** none