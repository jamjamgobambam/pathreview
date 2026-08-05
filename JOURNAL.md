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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback was provided during the Summer 2026 review
period. I therefore did not have any requested changes or comments to address.

**How you responded:**
No response or code changes were needed because no review feedback came in.

---

### Reflection

**What was harder than you expected?**
The hardest part was not writing the ownership query itself, but proving that a
small security fix behaved correctly within the existing test suite. The
repository had unrelated unit, tokenizer-download, lint, and type-check
failures, so a single red or green command was not enough to tell me whether my
change was safe. I had to separate the existing baseline from failures caused
by my branch and run the changed service and route tests independently. I also
had to learn that SQLAlchemy's async session returns a synchronous result
object: `db.execute()` is awaited, but `result.scalars().first()` is not. Using
`AsyncMock` for the whole chain made several existing tests model the API
incorrectly and produced confusing results.

**What did you learn about working in a large codebase?**
I learned that the correct fix depends on contracts outside the function where
the bug appears. The missing ownership check was in `create_review()`, but the
route also had to handle the service returning `None` before it accessed the
review ID or scheduled background processing. I used nearby profile and review
service functions to match the project's existing ownership-query pattern and
returned the same generic 404 for a missing profile and another user's profile
so the endpoint would not reveal whether a UUID exists. Compared with my own
projects, I spent more time tracing callers, matching established conventions,
limiting scope, and documenting baseline failures instead of changing every
related concern I noticed.

**How did AI tools help — and where did they fall short?**
AI tools were most useful for quickly locating the route, service, model, and
neighboring ownership checks; turning the security scenario into focused test
cases; and checking the diff for paths I might have missed. They also helped me
interpret noisy test output and recognize the difference between an
`AsyncMock` session method and the synchronous SQLAlchemy result returned by
that method. However, AI suggestions still needed verification against this
repository. They could not decide from generic advice whether this project
should use 403, 404, `None`, or an exception, and they could not treat a failing
full suite as proof that my patch was wrong or that it was safe. I had to read
the surrounding code, compare the branch with the repository baseline, run the
focused tests, and make the final scope and security decisions myself.

**What would you do differently if you started over?**
I would record the repository's test, lint, and type-check baseline immediately
after setup, before writing the reproduction. That would make later failures
much easier to classify. I would also map the service's callers before changing
its return contract and create the route-level test at the same time as the
service reproduction. The route test exposed an important requirement—an
unauthorized request must not enqueue `process_review`—that a service-only test
could not prove. Finally, I would confirm issue ownership in the cohort ledger
earlier because several contributors had expressed interest in the same issue.

**What are you most proud of from this module?**
I am most proud that I treated a short authorization fix as a complete behavior
change rather than just adding one `WHERE` clause. The final work verifies both
the allowed and rejected paths, avoids leaking profile existence, confirms that
rejected requests cause no database write or background task, and documents
exactly how the focused results differ from the repository-wide baseline. That
gave the contribution a clear, reviewable argument for why it is correct even
though the PR did not receive maintainer feedback.
