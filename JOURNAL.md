## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/163

**Issue title:** Review creation does not verify profile ownership

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

> Selection note: Issue #163 currently has only the `bug` label in the tracker. I
> am treating it as Tier 1-equivalent because the fix is localized, has a clear
> reproduction path, and follows ownership-query patterns already used by the
> neighboring review service functions.

**Problem summary:**
The review creation endpoint accepts a profile ID and passes the authenticated
user's ID into the review service, but the original service implementation did
not use that user ID to verify ownership. As a result, a signed-in user who knew
another user's profile UUID could potentially start a review for that profile.
The affected code is primarily `core/services/review_service.py`, with endpoint
error handling in `api/routes/reviews.py`. A successful fix will query for a
profile using both the profile ID and current user ID, refuse missing or
unauthorized profiles, and preserve normal review creation for the owner.

**Branch name:** `fix/163-review-profile-ownership`

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Issue-selection checklist reasoning

- **Scope:** The change is confined to review creation in one service and its API
  route, plus focused tests; it does not require a database migration or a new
  subsystem.
- **Understanding:** The insecure path is clear: `POST /reviews` supplies both
  IDs, while the service must enforce `Profile.id == profile_id` and
  `Profile.user_id == user_id` before constructing a `Review`.
- **Testing plan:** Add service tests for the owner, a different user, and a
  nonexistent profile, plus endpoint coverage confirming unauthorized profile
  IDs receive a not-found response and do not schedule background processing.
- **Dependencies and risk:** The implementation uses existing SQLAlchemy models
  and query patterns from `get_review()` and `list_reviews()`. No external API,
  schema migration, or AI model call is needed.
- **Time and fallback:** The core behavior is small enough to implement and test
  within the module timeline. If integration setup is blocked, the ownership
  rule can still be verified with mocked async database tests.
- **Claim check:** I commented on issue #163 from GitHub account `mikemaeda` on
  July 20, 2026. Multiple people have also expressed interest, so I will confirm
  availability in the cohort ledger and coordinate there before opening a PR.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [3b794c3 — failing ownership regression test](https://github.com/mikemaeda/pathreview/commit/3b794c3)

**Reproduction summary:**
I reproduced issue #163 with a focused unit test that treats an
ownership-scoped profile lookup as having no match. The test fails because
`create_review()` never executes that lookup and instead adds and commits a
pending review for the supplied profile ID.

**PLAN.md link:** [Solution plan](https://github.com/mikemaeda/pathreview/blob/fix/163-review-profile-ownership/PLAN.md)

**Walkthrough video (recommended):** Not recorded (recommended, not graded).

**Blockers or open questions:**
Confirm whether the upstream maintainers prefer the service to return `None` or
raise a domain-specific exception. The current plan follows the existing
`profile_service.get_profile()` convention and maps `None` to a generic 404 at
the route.
