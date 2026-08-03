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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed the service-level ownership check in `create_review()` and updated
the route to return 404 before scheduling background processing. Converted the
Week 8 failing reproduction into a passing regression test and added route-level
coverage for rejected and successful review creation.

**Next steps:**
Run the focused and repository-wide checks, document pre-existing failures,
self-review the diff against `docs/CONTRIBUTING.md`, and submit the upstream PR.

**Blockers:**
The repository-wide test and quality commands have unrelated pre-existing
failures. The review service and route tests pass independently.

---

### Check-in 2 (end of week)

**PR link:** [ascherj/pathreview#614](https://github.com/ascherj/pathreview/pull/614)

**Branch:** `fix/163-review-profile-ownership`

**What you built:**
Review creation now verifies that the requested profile belongs to the
authenticated user before writing anything. Missing or unowned profiles receive
the same generic 404 response, and rejected requests do not schedule background
review processing.

**Tests added or updated:**
Updated `tests/unit/test_review_service.py` to cover the ownership lookup and
no-write rejection path and to model synchronous SQLAlchemy results correctly.
Added `tests/unit/test_review_routes.py` to verify the rejected 404/no-task path
and the successful pending-review/task path; all 22 tests across those two files
pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

For this repository's documented baseline, "passes" means the contribution
introduces no new failures. The full unit run reports 39 unrelated failures,
361 passes, and 31 tokenizer-download setup errors; all changed-module tests
pass, and this branch removes 13 pre-existing review-service mock failures.
Repository-wide linting and typing also retain pre-existing errors, while Ruff
passes for the changed service and test files and Black reports all four changed
Python files are formatted.

**Draft PR feedback received from:** none
