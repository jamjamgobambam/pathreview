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

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
I reproduced the issue by tracing `POST /reviews` from `api/routes/reviews.py` into `core/services/review_service.py`. The route passes `current_user.id` into `create_review()`, but `create_review()` never checks `Profile.user_id`, so a review can be created for a profile owned by another user if the attacker knows that profile UUID.

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
I still need to confirm whether the rejected unauthorized request should return `404 Not Found` for consistency with existing profile/review endpoints, or `403 Forbidden` because the profile exists but belongs to another user.
