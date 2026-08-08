## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `POST /reviews` API route is missing a test for the case where a profile exists but has no ingested documents. Without that coverage, the endpoint could crash or return an unclear error and nobody would catch it. A successful fix adds a unit test (likely in `tests/unit/test_review_routes.py` or the existing review test files) that confirms the endpoint returns an appropriate error instead of failing unexpectedly. Scope is focused on tests for one edge case on the API layer, not a full feature rewrite.

**Branch name:** test/88-reviews-no-ingested-documents

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Selection notes — "Is this right for me?" checklist

| Check | Notes |
|---|---|
| Can I explain the bug in my own words? | Yes — profile exists, no ingested docs, review endpoint should error cleanly, and we need a test for that path. |
| Do I know which area of the codebase it touches? | Yes — API review routes + unit tests under `tests/unit/` (issue points at `test_review_routes.py`). |
| Is the scope small enough for Module 3? | Yes — Tier 1 / good first issue; estimated 2–3 hours; mostly adding one test case, not redesigning the review pipeline. |
| Do my skills match? | Yes — writing/asserting API unit tests is a good fit; I don't need deep RAG/agent work for this issue. |
| Is it still available / claimed? | I commented on the issue to claim it (AI 201 section 2a). Several others also commented, so I'll coordinate if needed and keep the work clearly scoped to the missing test. |
| Why this issue over others? | Clear acceptance criteria, named files, Tier 1, and it strengthens error-path coverage on a real API endpoint. |

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/kevin-luk-3/pathreview/commit/ab95557f99c6f5bca735433f795af50ac638ef38

**Reproduction summary:**
Confirmed the gap locally: `tests/unit/test_review_routes.py` does not exist, and no unit test covers `POST /reviews` when a profile has no ingested content. `create_review` / `create_review_endpoint` never check for `IngestedSource` rows (or empty ingestible profile fields) before creating a `pending` review, so the empty-content path is untested and has no intentional 4xx error contract yet.

**PLAN.md link:** https://github.com/kevin-luk-3/pathreview/blob/test/88-reviews-no-ingested-documents/PLAN.md


**Blockers or open questions:**
Still need to decide exact error contract (400 vs 404) and whether “no ingested content” means zero `IngestedSource` rows at POST time vs. a profile with no resume/github/portfolio fields. May need a small validation change in the route/service so the new test asserts real behavior, not only mocks.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Added a small empty-content check in `create_review_endpoint` (`api/routes/reviews.py`): load the profile with `get_profile`, return 404 if missing/not owned, return 400 if github/resume/portfolio are all empty. Added `tests/unit/test_review_routes.py` with one unit test for that 400 path. Left `review_service.py` / existing service tests unchanged.

**Next steps:**
Self-review against CONTRIBUTING.md, open a draft PR for peer/mentor feedback, then mark ready for review and paste the PR link into Check-in 2.

**Blockers:**
none

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/704

**Branch:** `test/88-reviews-no-ingested-documents`

**What you built:**
`POST /reviews` now returns 400 `"Profile has no ingested content to review"` when the profile has no github username, resume text, or portfolio URL, instead of creating a pending review. Missing/unowned profiles still get 404.

**Tests added or updated:**
- `tests/unit/test_review_routes.py` — asserts POST `/reviews` returns 400 when the profile has no ingestible content.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

**Notes for checkboxes above:**
Baseline comparison (stash our changes → run → restore → run again):
- `make test-unit`: before **53 failed / 375 passed**; after **53 failed / 376 passed** (same failures + our new passing test).
- `ruff check .`: **182 errors** before and after (unchanged).
- `mypy` (paths from Makefile): **5 errors** before and after (unchanged; further checking blocked by pre-existing issues).
Our contribution does not introduce new failures. "Passes" here means no new failures beyond that pre-existing baseline.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments on [PR #704](https://github.com/ascherj/pathreview/pull/704) by the end of Week 10 (no review comments, issue comments, or formal reviews). Per Su26 guidance, that’s okay — documenting the absence counts.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
The hardest part wasn’t writing the empty-content check itself — it was figuring out what “no ingested documents” actually meant in this codebase. Issue #88 sounded like counting `IngestedSource` rows, but those rows are created later inside `process_review`, so checking row count at `POST /reviews` time would reject almost every first review. Landing on “blank github/resume/portfolio fields” took reading `PLAN.md`, `_run_ingestion_pipeline`, and the route carefully. Pre-commit also blocked the commit with pre-existing ruff/mypy noise in `reviews.py` and imported services, which I didn’t expect on a Tier 1 test issue.

**What did you learn about working in a large codebase?**
In your own project you can rewrite freely; here a small issue still forces you to respect existing patterns and keep the diff tiny. My first attempt over-edited `test_review_service.py` (~200 lines of churn) when #88 only needed a route guard plus `tests/unit/test_review_routes.py`. Peer PRs and the issue’s “Relevant files” line made it clear: leave unrelated tests alone, put validation in `create_review_endpoint`, and don’t “fix” the whole suite. Also learned that `make format` / black on the whole repo can accidentally dirty dozens of files — restore those before committing.

**How did AI tools help — and where did they fall short?**
AI was useful for exploring `api/routes/reviews.py`, drafting the FastAPI `TestClient` test, and writing the PR/journal scaffolding. It fell short when it “helpfully” rewrote lots of existing service tests and suggested a bigger service-layer redesign than a good-first-issue needed — I had to push back, reset those files, and slim to ~20 lines in the route plus one new test file. It also couldn’t decide the product meaning of “ingested content” without me verifying against the live ingestion flow. AI drafts still needed a human scope check against CONTRIBUTING.md and the rubric.

**What would you do differently if you started over?**
I’d lock the empty-content definition in Week 8 (fields vs `IngestedSource`) before writing code, and I’d open a draft PR earlier instead of doing plan + implement + submit in a rush. I’d also run `make lint` / pre-commit on just the touched files first so I wasn’t surprised by B008/`Depends` and mypy failures that already existed in `reviews.py`. Finally I’d keep the first implementation minimal from day one instead of building a large service+test rewrite and then cutting it down.

**What are you most proud of from this module?**
I’m most proud of catching the overbuilt first approach and cutting it back to a reviewable Tier 1 PR: one validation block in `create_review_endpoint`, one unit test in `test_review_routes.py`, and a clear baseline note that we didn’t add to the 53 pre-existing unit failures. Shipping [PR #704](https://github.com/ascherj/pathreview/pull/704) with a small, intentional diff felt more like real open-source contribution than just getting something to pass locally.
