# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/163

**Issue title:** Review creation does not verify profile ownership

**Tier:** [ ] Tier 1 [x] Tier 2 [ ] Tier 3

**Problem summary:**
The `POST /reviews` endpoint passes the authenticated user's ID down to
`create_review()` in `core/services/review_service.py`, but that function never
actually uses it — it builds a `Review` straight from whatever `profile_id` the
request body supplied. That makes this a broken object-level authorization bug:
anyone who learns another user's profile UUID can create reviews attached to a
profile they don't own, because nothing ties the submitted `profile_id` back to
the caller. The inconsistency is easy to see in the same file, where
`get_review()` and `list_reviews()` both join `Profile` and filter on
`Profile.user_id == user_id` before returning anything. A successful fix makes
`create_review()` enforce that same ownership check — looking up the profile,
confirming it belongs to the authenticated user, and rejecting the request
otherwise — so the write path is scoped exactly like the read paths already are.

**Branch name:** `fix/163-review-profile-ownership`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### "Is this right for me?" — selection notes

- **Scope is bounded and legible.** The issue names the exact file and function,
  and the correct behavior already exists in the same module as a working
  reference. I am changing one function plus its tests, not designing anything
  new.
- **I can state the acceptance criteria myself.** Creating a review against a
  profile I don't own must fail with an authorization error; creating one
  against my own profile must keep working unchanged.
- **It is Tier 2 rather than Tier 1 because it crosses modules** — the API
  route, the service layer, and the `Profile`/`Review` models all have to agree
  on where the check lives and what error surfaces to the client. I chose it
  anyway because the cross-module reach is shallow and traceable, and the
  security framing makes it a more substantial thing to reason about and write
  up than a one-line attribute fix.
- **Risk I am watching:** picking the wrong layer for the check. Putting it in
  the route would leave the service insecure for any future caller, so the fix
  belongs in `create_review()` where the existing read-path checks already live.
- **Testing is straightforward.** The repo already has service-level tests, so I
  can add a case for the cross-user rejection alongside the existing happy path.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [9d6a50b](https://github.com/Kienda/pathreview/commit/9d6a50b76cbbf3ce4798b3de0842ee648938475f)

**Reproduction summary:**
I configured the review service test as if an ownership-scoped profile lookup found no
profile for the current user, then called `create_review()` with another user's profile
ID. The test fails because the service still creates and returns a pending review
instead of returning `None` without writing to the database.

**PLAN.md link:** [PLAN.md](https://github.com/Kienda/pathreview/blob/fix/163-review-profile-ownership/PLAN.md)

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
The current test suite has no endpoint integration-test harness, so I still need to
decide whether Week 9 route-level coverage belongs in `tests/security/` or should use a
smaller mocked route test alongside the service regression.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the ownership-scoped profile lookup in `create_review()`, added the route's
404 response for missing or unowned profiles, and prevented background processing from
being scheduled after rejection. The focused service and route tests pass.

**Next steps:**
Open the pull request, request peer or mentor feedback, address any applicable review
comments, and complete Check-in 2 with the final PR link and validation results.

**Blockers:**
The repository-wide suite currently has unrelated pre-existing failures, and GNU Make
is not installed in the local PowerShell environment. I ran the underlying pytest
command directly and confirmed the seven review-creation tests pass.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/409

**Branch:** `fix/163-review-profile-ownership`

**What you built:**
I added an ownership-scoped profile lookup before review creation. Missing and
unowned profiles now receive the same 404 response, no review is persisted, and
no background processing task is scheduled.

**Tests added or updated:**
Updated `tests/unit/test_review_service.py` with owned-profile success and
cross-user rejection coverage. Added `tests/unit/test_review_routes.py` to verify
that the endpoint returns 404 and does not schedule a background task when
ownership validation fails.

**Self-review confirmation:** [ ] make check passes [ ] make test-unit passes

The focused review-creation test suite passes with 7 tests passed and 14
deselected. Repository-wide checks report documented pre-existing failures
unrelated to this change.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in. PR #409 has been open on `ascherj/pathreview` since Week 9 and
still shows zero review comments and zero issue comments, and no maintainer has
requested changes or approved it. I checked the PR again at the end of Week 10 to
confirm before writing this entry.

**How you responded:**
No changes were required, so nothing was revised in response to feedback. I used
the week instead to re-read my own diff as a reviewer would and to confirm the
branch is still in a mergeable, reviewable state: the change remains scoped to
`create_review()` plus the route's 404 path, the seven focused review-creation
tests still pass, and the PR description still states the vulnerability, the
chosen enforcement layer, and the reasoning for returning 404 on both missing and
unowned profiles. If a maintainer comments after the course deadline, the
outstanding question I would expect — and would be ready to defend — is whether
404 or 403 is the right status for an unowned profile.

---

### Reflection

**What was harder than you expected?**
Writing the failing test before writing the fix. The fix itself was a short,
well-scoped change, but reproducing the bug as a test inside the repo's existing
fixture and mocking setup took the most effort. I had to make the test fail for
the *right* reason — because `create_review()` ignored the authenticated user and
persisted a review it should have rejected — rather than because I had wired the
profile lookup or the mocks incorrectly. Getting a red test that genuinely
described the authorization flaw was harder than making it green.

**What did you learn about working in a large codebase?**
The existing code is the spec. `get_review()` and `list_reviews()` in the same
module already did ownership scoping correctly by joining `Profile` and filtering
on `Profile.user_id == user_id`, so my job was not to invent an approach — it was
to make the write path match the pattern the read paths had already established.
On my own projects I decide the convention; here the convention already existed,
and the correct fix was the one that looked like it had always been there. That
also made the change easier to review, because a maintainer could see it as the
missing half of a pattern rather than as something new.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation. In an unfamiliar codebase it helped me locate
the relevant files quickly and understand how the route, the service layer, and
the `Profile`/`Review` models connected, which cut down the time between reading
the issue and being able to reason about it concretely.

Where it fell short was the judgment calls. Deciding that the check belonged in
`create_review()` rather than in the route, choosing to return 404 for both
missing and unowned profiles so the endpoint does not leak whether a profile
exists, and framing the issue as Tier 2 because it crosses modules — AI could lay
out the options, but it could not own those decisions or defend them in a pull
request. Those had to be mine, because I am the one who has to justify them.

**What would you do differently if you started over?**
I would sort out the test and tooling setup first. I did not confirm that GNU Make
was available or establish a clean baseline for the repository-wide suite until
Week 9, so verification turned into a late blocker instead of a background detail
— I ended up running the underlying pytest command directly and documenting
pre-existing failures under time pressure. Ten minutes of environment checks in
Week 7, before choosing the issue, would have removed that entirely.

**What are you most proud of from this module?**
Taking a real security bug all the way through. I found a broken object-level
authorization flaw in production code, reproduced it with a failing test, fixed
it at the layer where the check actually belongs, covered both the service and
the route, and submitted the PR upstream. The change is small, but the reasoning
behind it — why it is a vulnerability, where the enforcement goes, and what the
client should see — is entirely mine.
