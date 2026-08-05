## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents #88

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The POST /reviews endpoint doesn't have a test for what happens when a profile has no ingested documents. Right now we don't know if it fails properly or just crashes in this case. The fix is to add a test in tests/unit/test_review_routes.py that checks the endpoint returns a clear error instead of crashing when this happens. This affects the review routes part of the codebase and helps make sure the API handles this case safely.

**Branch name:** test/88-post-review-endpoint

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Moeez15/pathreview/commit/442a264df18ae33613bcefb898cf54c3b66bab7e

**Reproduction summary:**
Added a failing unit test (`test_process_review_with_no_ingested_documents` in `tests/unit/test_review_service.py`) that runs `create_review` + `process_review` for a profile with `github_username`, `portfolio_url`, and `resume_text` all `None`. Observed that `_run_ingestion_pipeline` correctly reports zero sources, but the downstream placeholder agent/RAG steps still fabricate feedback sections, and the review ends up `status="complete"` with a fake `overall_score` instead of failing or erroring.

**PLAN.md link:** https://github.com/Moeez15/pathreview/blob/test/88-post-review-endpoint/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
Need to confirm whether this issue is scoped to just adding a test documenting current behavior, or also expects a behavior fix (rejecting/failing reviews for empty profiles) in the same PR — see Risks & unknowns in PLAN.md.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Started on step 2 of PLAN.md: added a `profile_has_ingested_content(profile, db)` helper in `core/services/review_service.py` that checks `github_username`, `portfolio_url`, `resume_text`, and falls back to querying `IngestedSource` rows for the profile (to cover the stale-sources edge case noted in Risks & unknowns). Wired this into `process_review` (step 4) so that if `_run_ingestion_pipeline` comes back with zero sources, the review short-circuits to `status="failed"` with an `error_message` instead of continuing into `_run_agent_orchestration`/`_run_rag_retrieval_generation`. The existing reproduction test (`test_process_review_with_no_ingested_documents`) now passes against this change.

**Next steps:**
Decide on and implement the route-layer check in `create_review_endpoint` (step 3) so bad requests fail fast with a 400 instead of only failing after a background task runs. Then create `tests/unit/test_review_routes.py` (step 5) with endpoint-level tests, run `make check`/`make test-unit`, and open the PR.

**Blockers:**
Still not 100% sure whether the grading rubric expects the route-level 400 in addition to the service-layer failure, or if the service-layer fix alone satisfies the issue — going with "do both" per PLAN.md's Plan step 1 unless told otherwise.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/608

**Branch:** test/88-post-review-endpoint

**What you built:**
Added a `profile_has_ingested_content` check that runs both at request time in `create_review_endpoint` (returns a 400 with a clear error message before a `Review` row is created) and defensively inside `process_review` (marks the review `status="failed"` with `error_message` set if ingestion still comes back empty). This closes the gap where profiles with no GitHub/portfolio/resume content and no `IngestedSource` rows previously got a fabricated `status="complete"` review with fake feedback.

**Tests added or updated:**
- `tests/unit/test_review_service.py` — reproduction test flipped from failing to passing; added a second test covering the stale-`IngestedSource`-rows edge case.
- `tests/unit/test_review_routes.py` — new file; added a test asserting `POST /reviews` returns 400 with a descriptive error body for a profile with no ingested documents, and a control test confirming a profile with content still returns 201/pending as before.

**Self-review confirmation:** [X] make check passes (scoped to changed files)  [X] make test-unit passes (scoped to changed tests)

Note: repo-wide `make check`/`make test-unit` have pre-existing lint and test failures unrelated to #88 (documented in PLAN.md Risks & unknowns). Confirmed no new failures introduced: baseline was 57 failed/375 passed, now 53 failed/380 passed (4 fewer failures, 5 more passing, 0 new failures). `ruff check` and `black` are clean on every file I touched.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [X] Yes  [] No — still awaiting review

**Summary of feedback:**
No review comments yet on PR #608 as of writing this. Will update this section if/when feedback comes in.

**How you responded:**
N/A — nothing to respond to yet. In the meantime I re-ran `make check` and `make test-unit` one more time on my branch to make sure nothing had drifted since I opened the PR.

---

### Reflection

**What was harder than you expected?**
Honestly the actual fix (the `profile_has_ingested_content` check) was the easy part — figuring out *where* it belonged took longer than writing it. I went back and forth between just rejecting at the route layer vs. only failing inside `process_review`, and ended up doing both because I couldn't fully convince myself which one the issue actually wanted. Also didn't expect the pre-commit hooks to lint the whole file instead of just my diff — I had to clean up a bunch of pre-existing type/lint issues in `reviews.py` and `profile_service.py` that had nothing to do with #88 just to get the hook to pass.

**What did you learn about working in a large codebase?**
You can't just fix the bug in isolation — there's a whole existing pattern (mock usage in tests, `str` vs `UUID` typing across the service layer, the FastAPI `Depends()` style) that you either have to match or consciously deviate from. I also learned to check whether a test failure is actually caused by my change or was already broken before I touched anything — I almost assumed I broke something in `test_review_service.py` before realizing those 13 failures were pre-existing mock misuse, unrelated to my fix.

**How did AI tools help — and where did they fall short?**
AI was most useful for the boring-but-necessary stuff: writing the route-level tests, spotting the `str`/`UUID` mismatch pattern across the file, and quickly diffing before/after test counts to prove I didn't introduce regressions. Where it fell short was the judgment call on scope — deciding whether "add a test" in the issue title actually meant "and fix the behavior too" needed me to read the issue, the code, and make a call myself; that's not something I wanted to just hand off.

**What would you do differently if you started over?**
I'd ask a maintainer (or post in the issue thread) about scope *before* Week 8 instead of just noting it as an open question in PLAN.md and guessing. Would've saved me from second-guessing the "do both route check and service check" decision all the way through Week 9.

**What are you most proud of from this module?**
Catching the fabricated-review bug in the first place — the fact that a profile with literally nothing in it could get a "complete" review with a fake score is a real trust/safety issue, not just a missing test. Finding and reproducing that felt like actual debugging, not just busywork to satisfy the assignment.