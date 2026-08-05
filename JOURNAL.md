## Week 7 — Issue selection

**Issue link:** \
 https://github.com/ascherj/pathreview/issues/88


**Issue title:** \
POST /reviews endpoint has no test for when the profile has no ingested documents

**Tier:** Tier 1 was chosen to complete as a first open source contribution.

**Problem summary:** \
<!-- [In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.] -->
Issue #88 deals with the return of reviews when a profile has no added documentation such as github repo, or resume to provide feedback on. A test to administer to make the sure system does not crash with any ingested documentation is currently missing. By providing a test for the review output would ensure a successful fix of the system not crash. 

**Branch name:** \
test/88-post-review-endpoint

**Setup confirmation:** Yes App runs locally at localhost:5173

**Cohort ledger:** Yes Issue added to cohort ledger


**Is This Issue Right for me?:**\
- I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
- I've located the relevant files and confirmed they exist in the codebase.
- I can describe a concrete before-and-after: what the user sees before the fix and what they see after.
- I've found and read the specific code the issue references (not just the file — the function or section).
- I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
- I've found the test file for my module and read at least one test end-to-end.
- I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
- I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
- This issue has no open blockers or dependencies on other unresolved issues.



## Week 8 — Reproduction & solution planning

**Reproduction commit link:**

<!-- [link to commit documenting the reproduced issue] -->
https://github.com/Kiniec/pathreview/commit/b7af3beb36749ed1f6ef64191ed813dce58ea463

**Reproduction summary:**
<!-- 1–2 sentences: How did you reproduce the issue? What did you observe?-->

Ran the system locally with input of `user1@example.com` and received a review output. Traced the request path for POST /reviews (api/routes/reviews.py → review_service.process_review) to check for a crash when a profile has no ingested source documents. No exception is raised: _run_agent_orchestration/_run_rag_retrieval_generation return hardcoded sections regardless of input, so the review completes successfully with fake content instead of signaling that there was nothing to review.

**PLAN.md link:** 
<!-- [link to PLAN.md in your fork] -->
https://github.com/Kiniec/pathreview/tree/test/88-post-review-endpoint/PLAN.md

**Walkthrough video (recommended):** 
<!-- [link to your Loom video, ≤2 min — recommended, not graded] -->

**Blockers or open questions:**
<!-- [Anything you're still uncertain about going into Week 9, or leave blank] -->
One concern that has risen is the reproduction of the test. Should product code be changed to make the test works properly or should the test be able to perform with out any change to code in the codebase?



## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
<!-- [What have you implemented so far? Which sub-tasks from PLAN.md are done?] -->
 The subtasks of modifying and refactoring `api/routes/reviews.py` with a function of ` _has_ingested_documents()` which verify a profile has documents  and profile fetch/check in `create_review_endpoint()` which fetches profiles are before creating a review in the system.

**Next steps:**
<!-- [What are you working on for the rest of the week?] -->
Next steps are to review and work on implementing `test/unit/test_reviews_routes.py` and subtasks of Failing-case unit test with a mock Profile,  Happy-path regression test.

**Blockers:**
[Anything slowing you down? Or leave blank.]
none
---

### Check-in 2 (end of week)

**PR link:** 
<!-- [link to your submitted pull request] -->
https://github.com/ascherj/pathreview/pull/951

**Branch:** 
<!-- [the branch name you worked on, e.g. `fix/123-short-description`] -->
`test/88-post-review-endpoint`

**What you built:**
<!-- [1–3 sentences summarizing what your fix does and how it works] -->
 For this project, added a profile-fetch and no-documents check to create_review_endpoint() in `api/routes/reviews.py`. Reusing the existing g`et_profile()` service instead of adding any new fetch logic. Subsequently, the endpoint now can return 404 if the profile doesn't exist or isn't owned by the current user, and 400 if github_username, portfolio_url, and resume_text are all blank or whitespace-only. Both checks run before a review row is created or a background task is queued. There are no "pending" reviews left behind on a rejected request.

**Tests added or updated:**
<!-- [Which test files did you touch? What do they cover?] -->
 The files that were modified to changed the little in the production code. Added `tests/unit/test_reviews_routes.py` due to no test file previously existed for this route module.  Within `tests/unit/test_reviews_routes.py`, added 7 tests: three cover the _has_ingested_documents() helper directly (all-None, whitespace-only, one field populated), and four exercise create_review_endpoint() — 400 for a no-documents profile, 400 for whitespace-only fields, 404 for a profile that doesn't resolve. A happy-path regression confirming a profile with github_username set still creates and schedules the review. `tests/unit/test_review_service.py` was left untouched by design, since the check lives in the route layer, not `create_review()`. Git stash confirmed that its existing tests still pass unchanged.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Note: `make check`/`make test-unit` do not pass cleanly on this branch — both have pre-existing failures unrelated to this fix (confirmed via `git stash` comparison against the unmodified branch: same 53 test-unit failures and same ruff/mypy errors exist with or without my change). Committed with `--no-verify` for this reason. My own changes are clean: `api/routes/reviews.py`'s diff introduces zero new ruff violations, and the new `tests/unit/test_reviews_routes.py` passes ruff, black, and pytest with no failures.

**Draft PR feedback received from:** [name or Slack handle, or "none"]
none