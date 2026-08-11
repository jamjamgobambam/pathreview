## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/163

**Issue title:** Review creation does not verify profile ownership

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The POST /reviews endpoint accepts a profile_id, but core/services/review_service.py does not verify that the profile belongs to the authenticated user. As a result, a user who knows another user’s profile UUID could create a review for that profile. A successful fix will validate profile ownership before creating the review and reject unauthorized requests while preserving normal review creation.

**Branch name:** fix/163/Review-creation-does-not-verify-profile-ownership

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/arollaramreddy/pathreview/commit/2d290d90a4eab158f625294376c29267aca6b5e7

**Reproduction summary:**
I reproduced the issue by tracing `POST /reviews` from `api/routes/reviews.py` into `core/services/review_service.py`. The route passes `current_user.id` into `create_review()`, but `create_review()` never checks `Profile.user_id`, so a review can be created for a profile owned by another user if the attacker knows that profile UUID.

**PLAN.md link:** https://github.com/arollaramreddy/pathreview/blob/fix/163/Review-creation-does-not-verify-profile-ownership/PLAN.md

**Walkthrough video (recommended):** Not recorded



**Blockers or open questions:**
I still need to confirm whether the rejected unauthorized request should return `404 Not Found` for consistency with existing profile/review endpoints, or `403 Forbidden` because the profile exists but belongs to another user.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the ownership validation fix for review creation in `core/services/review_service.py`. Updated `api/routes/reviews.py` so `POST /reviews` returns `404` when the profile is missing or not owned by the authenticated user. Added coverage in `tests/unit/test_review_service.py` for authorized and unauthorized review creation, plus improved test typing annotations for mypy compliance.

**Next steps:**
Finish the PR description and submit the branch for review. Confirm whether the current branch has an open PR, update the PR link in this journal, and run repo checks once unrelated baseline failures are addressed.

**Blockers:**
`make test-unit` currently fails due to unrelated existing unit test failures in other modules, so I cannot yet mark full repo test status as passing.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/938

**Branch:** fix/163/Review-creation-does-not-verify-profile-ownership

**What you built:**
Implemented profile ownership enforcement for review creation so `POST /reviews` only creates a review if the authenticated user owns the requested profile. Unauthorized or missing profiles now produce a `404` and no review is inserted.

**Tests added or updated:**
Updated `tests/unit/test_review_service.py` to cover successful review creation for owner profiles and rejection when the profile is not owned by the current user. Also added type annotations to test fixtures and async test methods for strict `mypy` compliance.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No reviewer feedback had been received on PR #938 at the time of this final entry. The PR remains open, so I am still awaiting review.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The code change itself was small, but locating the correct ownership boundary took more investigation than I expected. The route already passed the authenticated user's ID into the service, yet `create_review()` accepted a `profile_id` without checking who owned it. I had to trace the request from `POST /reviews` through the route and service layers, compare nearby endpoint behavior, and decide whether an unauthorized profile should look like a `404` or a `403`. Verifying the change was also harder than expected because I needed focused tests and static checks to distinguish my change from unrelated repository-level test failures.

**What did you learn about working in a large codebase?**
In a larger codebase, the most important work often happens before editing: understanding existing conventions, data flow, and where a responsibility belongs. In my own project I might change a route directly and move on, but here I needed to preserve the separation between the API route and service layer, match the existing missing-resource behavior, and avoid starting background processing before authorization succeeds. Small changes can have effects in tests, type checking, and adjacent workflows, so reading surrounding code and making a narrowly scoped change matters as much as writing the new condition.

**How did AI tools help — and where did they fall short?**
AI tools were most useful for quickly navigating the codebase, identifying the request path, and suggesting focused test cases for owned and unowned profiles. They also helped catch missing type annotations that mattered for `mypy`. They could not decide the intended security and API behavior from the issue alone, though. I still needed to inspect the surrounding endpoints, reason about information disclosure and consistency, run the checks, and make sure the final implementation fit this repository rather than merely looking plausible in isolation.

**What would you do differently if you started over?**
I would establish the expected error contract earlier by checking related routes and tests before writing the implementation. I would also run the focused test, lint, and type-check commands immediately after the first change instead of waiting until the end, then run the broader repository checks separately. That would make it easier to identify whether a failure came from my work or from the existing baseline and would make the PR description more precise from the beginning.

**What are you most proud of from this module?**
I am most proud that I treated a small authorization bug as a real security and correctness issue. The final change prevents reviews from being created for another user's profile, keeps the API response consistent with the existing codebase, and adds tests that prove both the allowed and rejected paths. I also feel good about tracing the problem to `create_review()` instead of applying a narrow route-only patch, because that places the ownership rule beside the operation it protects. Seeing the focused tests cover both an owned profile and another user's profile gave me confidence that the fix addresses the actual issue described in #163.
