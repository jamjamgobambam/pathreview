## Solution plan

**Issue:** #88 — `POST /reviews` endpoint has no test for when the profile has no ingested documents — https://github.com/jamjamgobambam/pathreview/issues/88

### Understand
`create_review_endpoint` (api/routes/reviews.py:22-62) never loads the Profile
row and performs zero validation before creating a Review and scheduling the
`process_review` background task. That task (core/services/review_service.py:
82-194) runs four placeholder pipeline functions that ignore whether any real
content was ingested and always fabricate valid-looking sections and a score.
`_run_safety_checks` only validates the *shape* of the output (non-empty
name/content, confidence in [0,1]), never whether it's grounded in real data.
Net effect: a profile with no github_username, no portfolio_url, and no
resume_text still reaches status="complete" with fabricated feedback — no
crash, no error, anywhere in the pipeline. Confirmed live: registering a user,
creating a profile with zero fields, and creating a review for it reached
status="complete" with three fabricated sections and overall_score=0.81
within one poll (see JOURNAL.md Week 8 for the full transcript).

Expected vs. actual: Expected — a profile with nothing to review should be
rejected with a clear error before a Review is even created. Actual — the API
returns 200 immediately and the review always "succeeds" with made-up content.

**Root cause:** missing upfront validation in `create_review_endpoint`
(api/routes/reviews.py), compounded by placeholder pipeline stages in
`core/services/review_service.py` that don't check their own input.

### Map
Files I expect to touch:
- `api/routes/reviews.py` — `create_review_endpoint` (lines 22-62): fetch the
  Profile via `get_profile()` (not currently imported — need to add
  `from core.services.profile_service import get_profile`) and reject with
  422 if it has no ingested content, before calling `create_review()`.
- `core/services/profile_service.py` — add `profile_has_ingested_content(profile) -> bool`
  next to the existing `get_profile()` (lines 36-48), so the check lives in one
  place instead of being duplicated between the route and the service. Strip
  string fields before the truthiness check so whitespace-only values (e.g.
  `github_username=" "`) don't slip through — nothing in `api/schemas/profile.py`
  currently prevents submitting those.
- `core/services/review_service.py` — defense-in-depth: call the same helper
  near the top of `process_review`, right after the existing "profile not
  found" block (between lines 118 and 120), so a doomed review goes
  `pending → failed` directly instead of `pending → processing → failed`. Set
  `review.error_message` on this path (the `error_message` column already
  exists on the model and in `ReviewResponse` but nothing populates it today
  — decide whether the two pre-existing failure paths, lines 149-154 and
  182-194, get the same treatment as a drive-by fix, or are explicitly left
  for a separate issue).
- `tests/unit/test_review_service.py` — the Week 8 reproduction test
  (`test_no_ingested_content_should_not_produce_fabricated_review`) already
  lives here and currently fails as expected; will need a "profile with
  content still succeeds" regression test too once the fix lands (patch
  `process_review` to a no-op in that test — Starlette runs `BackgroundTasks`
  synchronously once the response is returned, so an unpatched test would
  actually execute all four placeholder stages for real).
- New: `tests/unit/test_review_routes.py` — first route-level test file in
  the repo. Use plain `TestClient(app)` (**not** `with TestClient(app) as
  client:`, which triggers `api/main.py`'s startup event and a real Postgres
  connection attempt — verified this empirically) with
  `app.dependency_overrides` for `get_current_user` and `get_db` (an
  `AsyncMock` session, same mocking idiom `test_review_service.py` already
  uses). Needs `@pytest.mark.unit` on the test class or `make test-unit`
  (which filters with `-m unit`) will silently collect zero of these tests
  while still exiting 0 — a real local/CI mismatch since CI's job has no
  such filter. Clear `app.dependency_overrides` in a fixture teardown so it
  doesn't leak into whichever test file loads next.

### Plan
1. Add `profile_has_ingested_content(profile) -> bool` to
   `core/services/profile_service.py`, stripping string fields before the
   truthiness check.
2. In `create_review_endpoint`, import and call `get_profile()` (404 if
   missing/not owned, matching the existing pattern in
   `get_profile_endpoint`), then call the new helper and raise
   `HTTPException(422, "Profile has no ingested content to review")` if it
   returns False — before calling `create_review()`.
3. Add the same helper call as a defense-in-depth guard near the top of
   `process_review`, setting `status="failed"` and `error_message` if
   reached with no content.
4. Build `tests/unit/test_review_routes.py`: plain `TestClient(app)` +
   `dependency_overrides` for `get_current_user`/`get_db`, `@pytest.mark.unit`
   on the class, teardown that clears overrides. Write the 422-rejection
   test and the profile-with-content regression test (with
   `process_review` patched to a no-op in the latter).
5. Run `make test-unit` and `make check` (lint/format/typecheck) to confirm
   everything passes before opening a PR.

### Inputs & outputs
- Function changing: `create_review_endpoint(data: ReviewCreate, ...)`.
- New behavior: if the `Profile` for `data.profile_id` has no
  `github_username`, no `portfolio_url`, and no `resume_text` (after
  stripping whitespace) → `HTTPException(422, detail="Profile has no
  ingested content to review")`, no `Review` row created.
- Existing happy path (profile with real content) is unchanged — verified by
  the regression test in step 4.

### Risks & unknowns
1. Route vs. service-layer placement: doing it in the route matches the
   existing 404 convention (`api/routes/profiles.py:122-133`) and 422
   convention (`api/routes/profiles.py:50-53`), but the service-layer
   defense-in-depth copy is still needed in case `create_review()` is ever
   called from somewhere other than this one route.
2. Building the first route/`TestClient` harness in this repo from scratch is
   real, non-trivial work — no existing pattern to copy, and the
   `with TestClient(...)`-triggers-real-DB gotcha above is exactly the kind of
   thing that silently eats an hour if not already known going in.
3. A `github_username` that's syntactically present but invalid/nonexistent
   still passes this check — this fix only catches "literally nothing
   provided," not "provided but ingestion would fail." Out of scope for #88
   as written, but a real boundary worth being explicit about in the PR
   description.
4. The two pre-existing failure paths in `process_review` (safety-check
   failure, generic exception handler) still don't populate `error_message`
   today — **decided (Week 9): left untouched.** Only the new
   no-ingested-content path sets `error_message`, keeping this PR scoped to
   issue #88; the gap on the two older paths is documented in the PR
   description as a candidate follow-up issue.

### Edge cases
- `resume_text=""` — already falsy in Python, handled for free.
- `github_username=" "` (whitespace-only) — NOT caught by a plain truthiness
  check; needs an explicit `.strip()` before the check.
- A profile updated after creation to remove its only content — checked the
  actual code: `update_profile` (profile_service.py) only overwrites fields
  `if data.X is not None`, and there's no endpoint to clear/re-upload
  `resume_text` after creation, so this isn't reachable through the app's own
  API today. Not a live risk, but the defense-in-depth check in
  `process_review` future-proofs it if a clear/patch endpoint is ever added.
- The "profile with content still succeeds" regression test must patch
  `process_review` to a no-op, since Starlette executes queued
  `BackgroundTasks` synchronously once the test client gets a response —
  otherwise the test silently runs all four real placeholder pipeline stages.

### Status (Week 9 — implemented)

All five plan steps are done. Verification against the pre-change baseline
(the repo has documented pre-existing failures; the requirement is
no *new* ones):

| Check | Baseline (before) | After fix |
|---|---|---|
| `pytest tests/unit -m unit` | 54 failed / 375 passed | 53 failed / 388 passed |
| `make typecheck` | 103 errors in 26 files | 103 errors in 26 files |
| `ruff check .` | 174 errors | 174 errors |
| `black --check` (my files) | — | all 4 touched/new files clean* |

\* `core/services/profile_service.py` and `core/services/review_service.py`
were already black-dirty before this change (pre-existing formatting on
untouched lines); the added lines themselves are black-clean.

The one failure that left the list is the Week 8 reproduction test, rewritten
to assert the fixed behavior (fails on pre-fix code, passes now — verified
both ways via `git stash`). The 53 remaining failures are byte-identical to
the pre-existing baseline set. Also verified end-to-end against the running
app: empty profile → 422 with a clear message, unknown profile → 404,
profile with content → 200 pending → completes as before.

One discovery worth noting for reviewers: 13 of the pre-existing failures in
`tests/unit/test_review_service.py` stem from a broken mocking idiom
(`AsyncMock` used for the *result* of `db.execute`, making the synchronous
`.scalars()` call return a coroutine). The new tests use a plain `Mock` for
result objects instead. The pre-existing tests were left untouched to keep
this PR scoped.
