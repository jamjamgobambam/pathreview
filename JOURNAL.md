# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/163

**Issue title:** Review creation does not verify profile ownership

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The POST /reviews endpoint forwards the authenticated user's ID into
`create_review()`, but the service layer ignores that argument entirely — it
builds a Review from the supplied `profile_id` without ever confirming the
profile belongs to the caller. This is inconsistent with the read paths
(`get_review` and `list_reviews`), which correctly scope every query through
`Profile.user_id`. As a result, an authenticated user who knows another
user's profile UUID can create reviews against that profile — a broken
object-level authorization (IDOR) vulnerability in `core/services/
review_service.py`. A successful fix will load the target profile, verify
`profile.user_id == user_id`, and return a 403 (or 404) when it doesn't
match, bringing review creation in line with the other endpoints.

**Branch name:** fix/163-review-ownership-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Is this right for me? — scope reasoning:**
- Scope is small and well-bounded: the root cause lives in a single function
  (`create_review`) in one service file, with the fix pattern already
  demonstrated by `get_review`/`list_reviews` in the same file.
- I can clearly explain the problem (missing ownership check) and what a
  correct fix looks like, and it is straightforward to test (a request with
  another user's profile_id should be rejected).
- No large architectural change or unfamiliar subsystem is required, so it
  fits comfortably within the module's timeframe.

## Week 8 — Issue reproduction & solution planning

**Reproduction steps:**
Wrote an integration test (`tests/integration/test_review_ownership.py`)
that drives the real FastAPI app end-to-end against the dev Postgres
database:
1. Register User A and User B via `POST /auth/register`.
2. As User B, create a profile via `POST /profiles` — note the `profile_id`.
3. As User A, call `POST /reviews` with `{"profile_id": "<User B's profile_id>"}`.

**What I actually saw:**
The request succeeded with `200 OK` and a full review object, e.g.:
```
AssertionError: Expected review creation to be rejected for a profile that
does not belong to the requesting user, got 200:
{"id":"281a7a24-2c1c-4476-a299-75d5af9a5b39", ...}
```
Server logs confirm it didn't just create the row — the background task ran
to completion against User B's profile on User A's behalf:
`review_processing_started` → `ingestion_pipeline_completed` →
`agent_orchestration_completed` → `review_processing_completed
overall_score=0.81`, all logged under `user_id` = User A but `profile_id`
belonging to User B. This confirms the issue exactly as described: no
ownership check exists between the authenticated user and the profile being
reviewed.

**Root cause:**
`create_review()` in `core/services/review_service.py` accepts a `user_id`
argument but never uses it — it builds the `Review` directly from the
caller-supplied `profile_id`. This is inconsistent with `get_review()` and
`list_reviews()` in the same file, which correctly filter on
`Profile.user_id`.

**Plan summary (full detail in `PLAN.md`):**
Reuse the existing ownership-scoped lookup,
`profile_service.get_profile(db, profile_id, user_id)`, inside
`create_review()`. If it returns `None`, raise `HTTPException(404)` —
matching the pattern already used by `get_review_endpoint` and
`get_profile_endpoint` for "not found or not owned," and avoiding a 403's
information leak about whether the profile exists at all.

**Files to touch:**
- `core/services/review_service.py` — add the ownership check in `create_review()`
- `api/routes/reviews.py` — confirm the 404 surfaces correctly from the route
- `tests/unit/test_review_service.py` — add a unit-level ownership test; update
  existing mocked tests that currently call `create_review()` without a
  matching `Profile`, since they'll break once the check is added

**Riskiest part:**
The existing unit tests in `test_review_service.py` mock `create_review()`
with unrelated random `profile_id`/`user_id` pairs and assert success —
several of those will need their mocks updated once the ownership lookup is
added, or they'll start failing for the right reason (they're exercising the
now-fixed vulnerable path).

**Status:**
- [x] Reproduction test written and confirmed failing (proves the bug)
- [x] `PLAN.md` completed
- [ ] Walkthrough video (optional, not recorded)

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from `PLAN.md`. `create_review()` in
`core/services/review_service.py` now calls
`profile_service.get_profile(db, profile_id, user_id)` and raises
`HTTPException(404)` if it returns `None`, matching the "not found or not
owned" pattern already used by `get_review_endpoint`/`get_profile_endpoint`.
Confirmed `api/routes/reviews.py` needed no change — it already re-raises
`HTTPException` before its generic 500 handler. Updated the 6 existing
`create_review` unit tests in `tests/unit/test_review_service.py` to mock
the new ownership lookup, and added
`test_create_review_rejects_profile_not_owned_by_user` for the cross-user
case. The Week 8 integration test
(`tests/integration/test_review_ownership.py`) now flips from failing (200)
to passing (404) — the fix works end-to-end.

Self-review: compared `make check`/`make test-unit` before and after the
change. Unit tests: `53 failed, 376 passed` both before and after — same 53
pre-existing failures, +1 new passing test, zero regressions. Ruff on the 2
files touched: 9 pre-existing errors before → 6 after (net-fixed 3 while
editing: unused import, a long line, import ordering). Mypy flags 13
pre-existing errors in `review_service.py`/`profile_service.py` (untyped
`db` params, `Any` returns) — verified via before/after diff that these are
identical violations at shifted line numbers, or in `profile_service.py`
(0 lines changed by us) surfacing only because our new import makes mypy
follow it. All sub-tasks 1–7 from `PLAN.md` are done; sub-task 8 (final
`make check`/`make test-unit` pass) is done modulo the documented
pre-existing failures above.

**Next steps:**
Commit and push the fix (using `--no-verify` for this one commit, since
pre-commit's mypy/ruff hooks block on the pre-existing debt documented
above — not on anything this change introduces). Open a draft PR with this
evidence in the description, request peer/mentor feedback in Slack, then
address feedback and mark the PR ready for review.

**Blockers:**
None blocking progress. Noting for transparency: pre-commit's mypy and ruff
hooks fail on pre-existing issues in `core/services/review_service.py` and
`core/services/profile_service.py` unrelated to issue #163 (untyped `db`
parameters, implicit-Optional defaults, `Any` returns, and
`N806`/`F841` in `get_review`/`list_reviews` tests we didn't touch). Verified
with before/after diffs that this change introduces zero new lint or type
errors; full breakdown will go in the PR description per the course's
pre-existing-failures guidance.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/687

**Branch:** fix/163-review-ownership-check

**What you built:**
`create_review()` in `core/services/review_service.py` now verifies the
requesting user owns the target profile before creating a review, by
reusing the existing scoped lookup `profile_service.get_profile(db,
profile_id, user_id)`. This closes the IDOR vulnerability in issue #163,
bringing `create_review()` in line with the ownership checks already used
by `get_review()`/`list_reviews()` in the same file. After Copilot review
feedback on the PR, revised the layering: `create_review()` now returns
`None` (rather than raising `HTTPException` from the service layer), and
`create_review_endpoint()` in `api/routes/reviews.py` translates that into
a 404 — matching the pattern `get_review_endpoint` already uses.

**Tests added or updated:**
- `tests/integration/test_review_ownership.py` (added Week 8): end-to-end
  reproduction test — registers two users, has one create a profile, and
  asserts the other is rejected (404) when requesting a review against it.
  Now passes (previously failed with 200); re-verified after the layering
  revision above.
- `tests/unit/test_review_service.py`: added
  `test_create_review_rejects_profile_not_owned_by_user` for the cross-user
  case (asserts `None` return, matching the revised layering); updated the
  6 existing `create_review` tests to mock the new `get_profile` ownership
  lookup; added a `_patched_get_profile()` helper to avoid duplicating mock
  setup; removed an unused `asyncio` import and an unused `mock_review`
  fixture (pre-existing dead code, surfaced while editing that test).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*("Passes" here means this change introduces zero new failures — see the
documented pre-existing lint/type/test debt in Check-in 1 and the PR
description, per the course's pre-existing-failures guidance.)*

**Draft PR feedback received from:** No peer/mentor response in Slack by
submission time. GitHub Copilot's automated review on PR #687 flagged 3
issues after the PR was marked ready: (1) service layer raising
`HTTPException` instead of returning `None` — fixed, see above; (2) an
unused `mock_review` fixture parameter — fixed, see above; (3) excluding
`tests/` from the local mypy pre-commit hook reduces local coverage —
replied on the PR explaining this matches CI's own typecheck scope
(`mypy api/ core/ ingestion/ rag/ agent/ safety/` never checked `tests/`
either), so no coverage gap versus CI was introduced; left as-is.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
No peer/mentor feedback came in through Slack. GitHub Copilot's automated
reviewer left 3 comments on PR #687 after it was marked ready: (1)
`create_review()` raised `HTTPException` directly from the service layer,
which breaks the codebase's own convention — every other service function
(`get_review`, `get_profile`) returns `None` and lets the route translate
that into an HTTP response; (2) a test fixture (`mock_review`) was passed
into a test but never used; (3) excluding `tests/` from the local mypy
pre-commit hook could hide real type regressions in test code.

**How you responded:**
Fixed (1) and (2) directly: `create_review()` now returns `None`, and
`create_review_endpoint()` raises the 404, matching `get_review_endpoint`'s
existing pattern; removed the now-fully-unused `mock_review` fixture
entirely rather than just the one parameter. For (3), I didn't just revert
it — I checked what CI's `typecheck` job actually runs
(`mypy api/ core/ ingestion/ rag/ agent/ safety/`) and confirmed it never
covered `tests/` either, so the local hook change didn't introduce a real
coverage gap versus what the project already enforces. Replied on the PR
explaining that reasoning instead of silently dropping the exclude. Both
code fixes are in commit `f988420`; re-ran the integration test afterward
to confirm the fix still worked end-to-end post-refactor.

---

### Reflection

**What was harder than you expected?**
Dealing with pre-existing tech debt turned out to be a bigger part of the
work than the actual fix. The repo already had 182 ruff errors across 52
files, a mypy setup that outright crashes on this machine's Python
3.14/numpy combination, and 53 failing unit tests — all before I touched
anything. Every time I tried to commit, pre-commit's hooks would block on
errors in files I was editing but hadn't introduced, and it wasn't always
obvious at a glance whether a given error was mine or already there. I
didn't expect "prove this isn't my fault" to be a real, recurring task
alongside writing the fix itself.

**What did you learn about working in a large codebase?**
That "make check passes" isn't the actual bar in a codebase with ambient
debt — "my change didn't make it worse" is. That distinction only holds up
if you can actually prove it, which meant repeatedly diffing before/after
states instead of eyeballing error counts. I also learned to follow the
codebase's existing conventions over what felt locally "correct" to me:
raising an HTTPException straight from the service layer felt natural
when I wrote it, but it broke a layering pattern the rest of the file
already used consistently, and Copilot's review caught that immediately.

**How did AI tools help — and where did they fall short?**
Fastest wins were navigating unfamiliar files, drafting tests that matched
existing patterns, and catching the service/route layering inconsistency
once it was pointed out. Where it fell short was exactly the thing that
mattered most: any claim of the form "this error is pre-existing, not
something we introduced" had to be independently verified — via
`git stash` and isolated before/after runs of ruff/mypy/pytest — rather
than trusted outright. A plausible-sounding claim and a verified one look
identical until you actually check, so that verification step became the
real discipline, not a nice-to-have. Bigger judgment calls — bypassing a
pre-commit hook, opening a PR against the real upstream repo instead of my
own fork — were ones I had to explicitly decide on, not just delegate.

**What would you do differently if you started over?**
I'd run `make check` and `make test-unit` on a clean checkout during Week 7,
before claiming an issue, so I knew the baseline debt existed up front
instead of discovering it mid-fix during Week 9 under more time pressure.
I'd also keep Docker Desktop running consistently through the week instead
of restarting it each session — small friction, but it interrupted my
verification flow more than once.

**What are you most proud of from this module?**
Not the PR itself, but how I handled Copilot's review comment about the
service layer raising `HTTPException`. My first instinct was that it was a
minor style nitpick, but I actually checked the rest of the file's
convention before responding, realized it was a real inconsistency, and
fixed the layering properly instead of dismissing an automated comment.
That felt like the actual skill this module was trying to teach.
