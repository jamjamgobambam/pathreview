## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/109

**Issue title:** Test coverage for core/services/review_service.py is below 40%

**Tier:** [x] Tier 2  [ ] Tier 1  [ ] Tier 3

**Problem summary:**
The `review_service.py` module orchestrates the entire review pipeline — fetching
a user's profile, running ingestion (GitHub, portfolio, resume), agent analysis,
RAG generation, and safety checks — but most of this logic currently has no unit
tests. This matters because `process_review` has several distinct outcomes (full
success, a missing profile, a failed safety check, and an unhandled exception
mid-pipeline) that each set the review's status differently, and none of that
branching logic is currently verified. A successful fix adds unit tests in
tests/unit/test_review_service.py that exercise each of these paths so future
changes to the pipeline don't silently break review processing.

**Branch name:** test/109-review-service-coverage

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/namitalamichhane/pathreview/commit/cb51d7f

**Reproduction summary:**
Ran `pytest tests/unit/test_review_service.py --cov=core.services.review_service --cov-report=term-missing`
and confirmed 22% coverage, below the 40% threshold in the issue. Coverage report shows
`process_review` (lines 98-194) and its helper functions `_run_ingestion_pipeline`,
`_run_agent_orchestration`, `_run_rag_retrieval_generation` (lines 202-279), and
`_run_safety_checks` (lines 369-390) are almost entirely untested. Also discovered
13 pre-existing tests for `get_review`/`list_reviews` are currently failing due to
an unrelated AsyncMock setup bug — noted as a blocker/observation, not part of this issue's scope.

**PLAN.md link:** https://github.com/namitalamichhane/pathreview/blob/test/109-review-service-coverage/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**
The 13 failing pre-existing tests are a separate bug (broken AsyncMock setup for db.execute).
Need to decide whether to leave them as-is or flag separately, since fixing them isn't part of issue #109's scope.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/695

**Branch:** `test/109-review-service-coverage`

**What you built:**
Added unit tests for `core/services/review_service.py`, focusing on `process_review`,
`_run_ingestion_pipeline`, and `_run_safety_checks`, which previously had almost no
coverage. Coverage for this file went from 22% to 90%.

**Tests added or updated:**
Added 15 new tests to `tests/unit/test_review_service.py`: 6 covering `process_review`
(success path and 5 failure/edge-case branches), 3 covering `_run_ingestion_pipeline`
(success, empty profile, partial source failure), and 6 covering `_run_safety_checks`
(valid output, missing sections, missing name/content, and confidence boundary values).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(13 pre-existing failures in `get_review`/`list_reviews` documented as out of scope;
confirmed no new failures or lint errors introduced by this change)

**Draft PR feedback received from:** [fill in once you hear back, or "none" if you submit before getting any]