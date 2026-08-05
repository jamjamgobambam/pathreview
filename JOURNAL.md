## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents
 

**Tier:** [Y] Tier 1  [ ] Tier 2  [ ] Tier 3
**Scope Reasoning**
[is this right for me?]
The issue is understandable, the reasoning behind it,as to why the review feature would be required, The consequences of not fixing it and what a successful fix looks like are all clear and explained clearly. The surrounding context and related file have been accessed.
The ideal fix has been decided.

**Problem summary:**
The POST /reviews endpoint has no test covering the case where a profile has no ingested documents. It doesn't crash — it silently succeeds, which is worse: `_run_ingestion_pipeline`correctly returns zero sources, but `process_review` never checks that before continuing, so the review is marked `complete` with fabricated sections and a score built from no real data. A successful fix adds that check, returns an honest response instead of invented feedback,
and includes a test verifying it.
**Branch name:** 
fix/88-no-profile-associated-ingested-content-review-endpoint

**Setup confirmation:** [Yes ] App runs locally at localhost:5173

**Cohort ledger:** [ Yes] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 
https://github.com/rohitpeets/pathreview/commit/9379711

**Reproduction summary:**
I reproduced this issue by calling 'process_review' (in 'core/services/review_service.py') directly against a 'No Ingested document' state with a mocked async DB session , a profile with github_username=None,portfolio_url=None, and resume_text=None.
This was possible because every source field in profileCreate is optional with no 

_run_ingestion_pipeline` correctly returned zero sources, but `process_review` still marked the review `status="complete"` with 3 fabricated sections and `overall_score=0.81`, and the safety checks passed it.

The Issue reproduction pytest lives at 'tests/unit/test_issue88_reproduction.py'.

**PLAN.md link:**
https://github.com/rohitpeets/pathreview/blob/fix/88-no-profile-associated-ingested-content-review-endpoint/PLAN.md


**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to confirm the intended contract for the zero-source case — reuse status="failed" with
an error_message, add a new status, or reject at the endpoint with a 4xx. The issue also
names tests/unit/test_review_routes.py, which doesn't exist yet, so I need to confirm whether route-level coverage is expected in addition to the service-level reproduction.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

Implemented the guard in `create_review_endpoint` (PLAN.md sub-task 2) and wrote `tests/unit/test_review_routes.py` (sub-task 3), the file named in the issue. Recorded baseline `make check` and `make test-unit` numbers before changing anything so I could prove my changes introduce no new failures (sub-task 5).

**Next steps:**

Open the PR, document the pre-existing failures, and confirm with the maintainer whether 422 is the status code they want for the empty-profile case.

**Blockers:**

PLAN.md sub-task 1 — confirming the intended contract on the issue thread — did not happen before I started building. The issue asks for a test that the endpoint "returns an appropriate error rather than crashing," but reproducing it showed the endpoint does neither: it silently succeeds with fabricated feedback. The error had to exist before it could be tested, so I raised the question in the PR description instead.

---

### Check-in 2 (end of week)

**PR link:**

**Branch:** `fix/88-no-profile-associated-ingested-content-review-endpoint`

**What you built:**

`POST /reviews` now verifies the target profile before creating anything: 404 if the profile does not exist or is not owned by the caller, 422 if it exists but has no ingested documents. Both checks run before `create_review`, so no pending review row is written and no background task is queued for a profile with nothing to analyse.

**Tests added or updated:**

Added `tests/unit/test_review_routes.py` with 8 tests covering an empty profile (422, and no review row created), whitespace-only source fields, each of the three source types individually being accepted, a missing or unowned profile (404), and that the profile lookup is scoped to the authenticated user. Removed `tests/unit/test_issue88_reproduction.py`, the Week 8 reproduction test, since its assertions described the pre-fix behaviour.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both commands fail on `main` for reasons unrelated to this issue, and my changes introduce no new failures. `make check` reported 182 ruff errors before and 181 after — one lower because I removed an unused `Review` import from the file I edited. `make test-unit` reported 53 failed / 376 passed before and 53 failed / 383 passed after: the same 53 failures, plus my 8 new tests, minus the removed reproduction test.

**Draft PR feedback received from:** none