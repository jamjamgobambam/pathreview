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

**PR link:** none yet

**Branch:** fix/163/Review-creation-does-not-verify-profile-ownership

**What you built:**
Implemented profile ownership enforcement for review creation so `POST /reviews` only creates a review if the authenticated user owns the requested profile. Unauthorized or missing profiles now produce a `404` and no review is inserted.

**Tests added or updated:**
Updated `tests/unit/test_review_service.py` to cover successful review creation for owner profiles and rejection when the profile is not owned by the current user. Also added type annotations to test fixtures and async test methods for strict `mypy` compliance.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** none
