# PathReview Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`tests/unit/test_review_routes.py` doesn't exist yet, so there is no route-level
test coverage for `POST /reviews` at all, including the case where a profile
has no ingested content. While tracing the code (`api/routes/reviews.py`,
`core/services/review_service.py`), I found that the endpoint doesn't actually
validate document presence anywhere: `create_review` always creates a
`status="pending"` review and returns 200 regardless of the profile's state,
and the background `process_review` pipeline produces placeholder feedback
and marks the review "complete" even when zero sources were ingested. A
successful fix for this ticket, scoped narrowly, is a test that documents
this real current behavior for a profile with no ingested sources; adding an
actual error response for that case would be a separate, larger change to
the route/service layer.

**Branch name:** test/88-review-no-ingested-documents

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Reproduction:**

Confirmed both halves of the problem summary hands-on, no server/DB required.

1. Coverage gap — `tests/unit/test_review_routes.py` does not exist:
   ```
   $ find tests -iname '*review_routes*'
   (no output)
   ```
   `tests/unit/` only has `test_review_service.py`; `tests/integration/` is
   empty aside from `__init__.py`. There is no route-level test for
   `POST /reviews` at all, let alone the no-ingested-documents case.

2. Behavior gap — ran `process_review()` directly against a `Profile` with
   `github_username=None`, `portfolio_url=None`, `resume_text=None` (zero
   ingested sources), using the same in-memory mock-session style already
   used in `test_review_service.py`:
   ```
   ingestion_pipeline_completed   sources_count=0
   ...
   review_processing_completed    overall_score=0.81

   Final review.status        = 'complete'
   Final review.overall_score = 0.81
   Number of feedback sections returned = 3
   ```
   Despite 0 ingested sources, the review still ends up `status="complete"`
   with 3 fabricated feedback sections and a fake score. Root cause is in
   `core/services/review_service.py`:
   - `create_review` (line 15) never checks for ingested sources before
     returning `status="pending"`.
   - `_run_agent_orchestration` (line 282) and
     `_run_rag_retrieval_generation` (line 307) return hardcoded placeholder
     sections and ignore `ingestion_results` entirely, even when it's `[]`.
   - `_run_safety_checks` (line 357) only validates structural shape
     (non-empty strings, confidence in range), so the placeholder output
     always passes.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/wvalera1/pathreview/commit/d0193c363ec9f2b77f009b78d154ba64cd740d7e

**Reproduction summary:**
Ran `process_review()` directly against a `Profile` with no `github_username`,
`portfolio_url`, or `resume_text` (zero ingested sources) using an in-memory
mock DB session; observed the review still finishes `status="complete"` with
3 fabricated feedback sections and a fake 0.81 score, confirming the endpoint
and background pipeline do no document-presence validation.

**PLAN.md link:** https://github.com/wvalera1/pathreview/blob/8c0be0d1d21557af98001d163477965e1c6aa7d8/PLAN.md
