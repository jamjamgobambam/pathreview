## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/163

**Issue title:** Review creation does not verify profile ownership

**Tier:** [ ] Tier 1 [X] Tier 2 [ ] Tier 3

**Problem summary:**
The `POST /reviews` endpoint lets any logged-in user create a review for a profile just by passing its ID, without checking that the profile actually belongs to them. The bug lives in `create_review()` in `core/services/review_service.py`, which trusts the supplied `profile_id` even though the read functions (`get_review()`, `list_reviews()`) in the same file already filter by `Profile.user_id`. This is a broken-access-control (IDOR) vulnerability: knowing another user's profile UUID is enough to create reviews on their data. A successful fix adds an ownership check so that requests for a profile the user doesn't own are rejected (e.g. 403/404), and a regression test confirms the attack is blocked.

**Branch name:** fix/163-review-creation-profile-ownership-error

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**Is this right for me? checklist reasoning:**

- **Understanding:** I can explain it in my own words and I know the "done" state — before: a user can create a review on someone else's profile by passing its ID; after: that request is rejected (403/404) and only the owner can create a review. Before/after is concrete and testable.

- **Tier fit:** Tier 2 is a stretch for a first contribution, but the scope is narrow — the fix is confined to `create_review()` in `core/services review_service.py`, and the exact pattern I need (`Profile.user_id == user_id`) already exists in `get_review()` and `list_reviews()` in the same file. So it reads like a Tier 1-sized change with Tier 2 cross-module context (auth → profile → review). Comfortable, not over my head.

- **Codebase readiness:** I've read the three service functions and confirmed the bug: `create_review()` takes `user_id` but never filters by it. The test file `tests/unit/test_review_service.py` exists, so I have existing tests to model my regression test on.

- **Scope & time:** Small, well-bounded change plus one test — realistic within the Week 8–9 window alongside other commitments. No blockers or dependencies listed on the issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** <!-- TODO: paste the GitHub link to this Week 8 commit after pushing, e.g. https://github.com/EMP-Kritazya/pathreview/commit/<sha> -->

**Reproduction summary:**
I reproduced issue #163 by driving `create_review()` (in `core/services/review_service.py`)
directly with a mismatched pair — an attacker `user_id` and a victim `profile_id` the
attacker does not own — while tracking whether the service performs any ownership lookup.
Observed: `create_review()` never issued an ownership query (`db.execute` was never called),
called `db.add`, and returned a persisted `pending` review anyway. This confirms the IDOR:
any authenticated user can create a review against another user's profile just by knowing
its UUID, because `create_review()` accepts `user_id` but ignores it. The read paths
(`get_review`, `list_reviews`) already scope by `Profile.user_id`, so only the create path
is unprotected.

**Reproduction steps:**

1. From the fork root (`pathreview/`), with the app's virtualenv, call `create_review(db, profile_id, user_id)` with `profile_id` and `user_id` that do not correspond to the same profile (mocked DB session, patched `Review`).
2. Assert whether any ownership `SELECT` is issued before the write.
3. Observed result: no ownership check, `db.add` called, a review returned — i.e. the review is created for a profile the caller does not own.

**PLAN.md link:** [PLAN.md](./PLAN.md) <!-- on GitHub: https://github.com/EMP-Kritazya/pathreview/blob/fix/163-review-creation-profile-ownership-error/PLAN.md -->

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
Deciding between `404` (matches `get_review`/`get_profile`, avoids leaking profile existence)
and `403` for the rejected case — leaning `404` for consistency. Also whether to fix the
pre-existing `AsyncMock().scalars()` failures in `tests/unit/test_review_service.py` as part
of this PR or keep them out of scope (leaning out of scope).

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week, 2026-08-04)

**Current progress:**
All 5 steps of PLAN.md are implemented and locally verified:

1. `create_review()` in `core/services/review_service.py` now calls
   `profile_service.get_profile(db, profile_id, user_id)` before constructing a
   `Review`, and returns `None` when the profile is missing or not owned.
2. `create_review_endpoint()` in `api/routes/reviews.py` checks for that `None`
   and raises `HTTPException(404, "Profile not found")` before queuing the
   `process_review` background task — matching the `404` decision noted as an
   open question in the Week 8 entry.
3. Added the regression test `test_create_review_returns_none_for_unauthorized_profile`
   in `tests/unit/test_review_service.py`, plus updated the other `create_review`
   tests to mock `get_profile` (they now patch it to return an owned profile so the
   happy path still exercises `Review` construction). Also replaced the `AsyncMock().scalars()`
   pattern with plain `Mock()` for `.scalars()` across the file, which resolves the
   pre-existing mock-quirk failures flagged in Week 8 — so that "leaning out of scope"
   call ended up moot, since it was needed to make the new/adjacent tests reliable.
4. Verified the happy path manually against the running API (docker-compose postgres
   - uvicorn): registered two users, created a profile for each, confirmed
     `POST /reviews` with another user's `profile_id` returns `404` and creates nothing,
     and `POST /reviews` with the caller's own `profile_id` returns `200` and the
     background task completes the review end-to-end.
5. `make test-unit`: 20/20 tests pass in `tests/unit/test_review_service.py`; full
   suite is 389 passed / 40 failed, and I confirmed those 40 failures are pre-existing
   and unrelated (bias*detector, pii_scrubber, tech_detector, etc. — none touch
   review/profile code) by running the same suite before my changes (53 failed / 375
   passed at baseline — my change actually \_fixes* 13 of those, the ones caused by the
   mock-quirk in `test_review_service.py`). `make check` passes with no new lint/type
   errors introduced; two pre-existing mypy/type gaps in files I touched
   (`User.id`/`Review.id` stored as `str` vs. the `UUID` params services expect, and
   `Review.sections` typed as `dict | None` while `process_review` stores a list) were
   fixed or explicitly annotated as pre-existing so the pre-commit hook's mypy check
   passes without silently masking unrelated bugs.

**Next steps:**
Push the branch, open the PR against `ascherj/pathreview`, and fill in the PR
template (including the pre-existing-failures note above). Also want to re-read
`docs/CONTRIBUTING.md` once more for docstring conventions before opening the PR.

**Blockers:**
None — the only snag was the local pre-commit hook (ruff/mypy) failing on
pre-existing issues in the files I touched; resolved with minimal, behavior-preserving
type annotations rather than skipping the hook.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/912

**Branch:** `fix/163-review-creation-profile-ownership-error`

**What you built:**
`create_review()` in `core/services/review_service.py` now checks profile ownership
before creating a review, by reusing the existing `profile_service.get_profile(db,
profile_id, user_id)` lookup that already scopes by `Profile.user_id`. If the
profile doesn't exist or isn't owned by the caller, `create_review()` returns
`None` and `create_review_endpoint()` in `api/routes/reviews.py` responds `404`
before any background processing is queued — closing the IDOR in issue #163
without touching the read paths, which were already safe.

**Tests added or updated:**
`tests/unit/test_review_service.py` — added
`test_create_review_returns_none_for_unauthorized_profile` (asserts `create_review`
returns `None` and never calls `db.add`/`commit`/`refresh` for a profile the caller
doesn't own). Updated the other `create_review` tests to mock `get_profile` so the
happy path still exercises `Review` construction, and replaced the
`AsyncMock().scalars()` pattern with plain `Mock()` for `.scalars()` throughout the
file, fixing several pre-existing mock-quirk failures unrelated to #163 along the
way.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes
(40 pre-existing, unrelated failures documented in the PR description — confirmed
against a pre-change baseline of 53 failed/375 passed; this branch is 40 failed/389
passed, so no new failures and 13 fewer than baseline)

**Draft PR feedback received from:** none yet

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [X] No — Su26 note: reviewer feedback is not a
feature this term, so no review is expected on PR #912.

**Summary of feedback:**
No feedback came in — reviewer feedback is not enabled for Summer 2026, per
the course note for this week. PR #912 remains open with no comments.

**How you responded:**
N/A — nothing to respond to. In its absence, I did my own second pass on the
diff before finalizing Week 9's Check-in 2 (re-reading `create_review()`,
`create_review_endpoint()`, and the new/updated tests end to end) to catch
anything a reviewer likely would have flagged.

---

### Reflection

**What was harder than you expected?**
Telling apart "my change broke this" from "this was already broken" was
harder than I expected. When `make test-unit` came back 40 failed / 389
passed after my change, my first instinct was that I'd introduced 40
regressions. It took running the full suite against the unmodified branch
(53 failed / 375 passed) to see that my change actually netted 13 _fewer_
failures, because replacing `AsyncMock().scalars()` with `Mock()` in
`test_review_service.py` incidentally fixed a mock-quirk that was failing
unrelated tests. Without that baseline comparison I would have either
panicked or, worse, tried to "fix" failures that had nothing to do with
issue #163. The 403-vs-404 decision was a smaller version of the same
problem: it wasn't obvious until I checked that `get_review()` already used
404 for the equivalent case, so consistency with the existing pattern
settled it rather than my own judgment.

**What did you learn about working in a large codebase?**
The biggest lesson was that the fix was already half-written elsewhere in
the file. `get_review()` and `list_reviews()` in `review_service.py` already
filtered by `Profile.user_id` — the bug was that `create_review()` never
called the equivalent `profile_service.get_profile(db, profile_id,
user_id)` check. In my own projects I'd probably have written a fresh
ownership check inline; here, reusing the existing helper kept the fix
small and consistent with the codebase's conventions instead of adding a
second way of doing the same thing. I also learned to draw a hard line
around scope — I was tempted to fix all 40 pre-existing failures
(bias_detector, pii_scrubber, tech_detector) since I was already in the
test suite, but they were unrelated to #163 and touching them would have
bloated the PR and made it harder to review, so I documented them instead
of fixing them.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the mechanical parts: scaffolding the
reproduction script that called `create_review()` directly with a
mismatched `user_id`/`profile_id` pair, and drafting the regression test
`test_create_review_returns_none_for_unauthorized_profile` to match the
existing test file's mocking conventions. It fell short on the judgment
calls — deciding 404 vs. 403, deciding whether the pre-existing
`AsyncMock().scalars()` failures were in scope to fix, and reasoning
through the `User.id`/`Review.id` `str`-vs-`UUID` mypy gaps so the fix was
correct rather than just quiet. Those needed me to actually read the
surrounding code and the codebase's own precedent, not just generate
something plausible.

**What would you do differently if you started over?**
I'd establish the pre-existing-failures baseline (`make test-unit` on the
unmodified branch) in Week 8 during reproduction, not in Week 9 right
before the PR. I ended up doing it reactively once I saw 40 failures and
got worried, but doing it up front would have saved the mid-week scramble
and let me state "N pre-existing failures, none touching review/profile
code" with confidence from the start instead of backfilling the evidence.

**What are you most proud of from this module?**
Catching that my fix incidentally repaired 13 unrelated test failures, and
resisting the urge to expand the PR to "clean up" the other 40 — instead
documenting both clearly in the PR description. That distinction between
what's honestly in scope and what's just nearby felt like the most
professional judgment call of the whole four weeks.
