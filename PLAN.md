# Solution plan

**Issue:** Review creation does not verify profile ownership — https://github.com/ascherj/pathreview/issues/163

## Understand

**Root cause.** `create_review()` in `core/services/review_service.py` accepts a
`user_id` argument but never uses it. It builds a `Review` directly from the
caller-supplied `profile_id` and persists it, without ever checking that the
profile belongs to `user_id`. There is no `db.execute` / ownership query in the
function at all (confirmed at runtime — see reproduction).

This is a broken-access-control / IDOR (Insecure Direct Object Reference) bug.
It is also _inconsistent_ with the rest of the module: `get_review()` and
`list_reviews()` in the same file already scope every read through
`Profile.user_id == user_id`, and `profile_service.get_profile()` does the same
for profiles. Only the create path skips the check.

**Expected vs. actual behavior**

- **Actual:** An authenticated user sends `POST /reviews {"profile_id": "<another
user's profile id>"}` and receives `200 OK` with a new `pending` review created
  against a profile they do not own. A background `process_review` task is then
  queued against that profile.
- **Expected:** A request for a profile the caller does not own is rejected with
  `404 Not Found` (consistent with `get_review` / `get_profile`, which return 404
  for non-owned resources and avoid leaking whether the profile exists). No review
  is created and no background task is queued.

## Map

Files/functions I expect to touch or rely on:

| File                                              | Symbol                                               | Role in the fix                                                                                                                                                                                     |
| ------------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `core/services/review_service.py`                 | `create_review()` (lines 15–32)                      | **Primary change.** Add an ownership check before creating the `Review`.                                                                                                                            |
| `core/services/profile_service.py`                | `get_profile(db, profile_id, user_id)` (lines 36–48) | **Reuse.** Returns `None` when the profile is missing or not owned — exactly the check I need. Import and call it.                                                                                  |
| `api/routes/reviews.py`                           | `create_review_endpoint()` (lines 22–62)             | Handle the rejected case: when the service signals "not owned", raise `HTTPException(404)` (mirroring `get_review_endpoint`) instead of proceeding to `model_validate` / queueing `process_review`. |
| `tests/unit/test_review_service.py`               | new regression test                                  | Add a test asserting `create_review` does **not** persist / return a review for a profile the caller does not own.                                                                                  |
| `core/models/profile.py`, `core/models/review.py` | (read-only)                                          | Confirm `Profile.user_id` and `Review.profile_id` field names used in the check.                                                                                                                    |

## Plan

1. **Reuse the ownership check in the service.** In `create_review()`, before
   constructing the `Review`, call `get_profile(db, profile_id, user_id)`. If it
   returns `None`, do not create anything — return `None` (matching the
   `X | None` return contract already used by `get_review`). Import `get_profile`
   from `core.services.profile_service`.
2. **Reject cleanly at the route.** In `create_review_endpoint()`, check the
   service result; if it's `None`, raise `HTTPException(status_code=404,
detail="Profile not found")` and log a `warning` — the same shape as
   `get_review_endpoint`. Because this is raised before `background_tasks.add_task`,
   no `process_review` job is queued for a non-owned profile.
3. **Add a regression test.** In `tests/unit/test_review_service.py`, add
   `test_create_review_rejects_profile_not_owned_by_user`: an attacker `user_id`
   with a victim `profile_id`, assert `db.add` is not called and no review is
   returned. Also keep/adjust a happy-path test proving an owned profile still
   creates a review.
4. **Verify the happy path is untouched.** Manually confirm via the running API
   (register user → create profile → `POST /reviews` with own profile) that a
   normal review still returns `200` and processes.
5. **Run the suite and linters.** `make test-unit`, then `make check`
   (ruff + black + mypy) before opening the PR.

## Inputs & outputs

- **Input:** `create_review(db, profile_id: UUID, user_id: UUID)` — the
  authenticated user's id (from `get_current_user`) and the requested profile id
  (from the `ReviewCreate` body).
- **Output (owned profile):** unchanged — a persisted `Review` with
  `status="pending"`, returned and serialized as `ReviewResponse` (`200`); a
  `process_review` background task queued.
- **Output (not owned / missing profile):** no `Review` created, no background
  task queued; the endpoint responds `404 Not Found`.
- **Side effects changed:** one added ownership `SELECT` on `Profile` per create;
  `db.add`/`commit`/`refresh` only run when ownership passes.

## Risks & unknowns

- **404 vs 403.** I plan `404` to match `get_review`/`get_profile` (don't leak
  existence). A `403` would arguably be more semantically precise; I'll follow the
  repo's existing convention and can revisit if a maintainer prefers 403.
- **Where the check lives.** Doing it in the service (`create_review`) vs. the
  route. I chose the service so the ownership guarantee holds for any future
  caller, consistent with how reads are scoped. Risk: the route's broad
  `except Exception -> 500` in `create_review_endpoint` would swallow a `None`
  into a 500 if I forget the explicit `if not review` check — step 2 addresses
  this directly.
- **Extra DB round-trip.** Reusing `get_profile` adds one `SELECT`. Negligible for
  a create endpoint, and it mirrors `update_profile`/`delete_profile`, which
  already do this.
- **Pre-existing test noise.** `tests/unit/test_review_service.py` currently has
  failing tests due to an `AsyncMock().scalars()` returning a coroutine under the
  installed pytest/mock versions — unrelated to #163. My new test must use a plain
  `Mock` result (not `AsyncMock`) so its pass/fail reflects the bug, not the mock
  quirk. Unknown: whether to fix those pre-existing failures here or leave them out
  of scope (leaning out of scope to keep the PR focused).
- **`process_review` also trusts `profile_id`.** It fetches the profile without a
  `user_id` scope. Once creation is guarded, an unowned profile can no longer reach
  it, so I'll leave `process_review` unchanged but note it in the PR.

## Edge cases

- **Profile belongs to another user** — the core exploit → `404`, nothing created.
- **`profile_id` does not exist at all** — `get_profile` returns `None` → `404`
  (same path, no separate branch needed).
- **Profile belongs to the caller** — happy path unchanged → `200`, review created.
- **Well-formed UUID that simply isn't theirs** — passes Pydantic `UUID`
  validation but fails ownership → `404` (validation ≠ authorization).
- **Malformed / missing `profile_id`** — rejected earlier by `ReviewCreate`
  schema validation → `422`; my change doesn't affect this.
- **Unauthenticated request** — already `401` via `get_current_user`; unchanged.
