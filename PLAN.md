## Solution plan

**Issue:** https://github.com/ascherj/pathreview/issues/163

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

`create_review()` in `core/services/review_service.py` accepts a `user_id` argument but
never uses it — it builds a `Review` directly from the supplied `profile_id` with no
query against `Profile` at all. This means `POST /reviews` will happily create a review
against a profile owned by a *different* user, as long as the caller knows or guesses
that profile's UUID (an IDOR / broken object-level authorization bug).

Expected: `create_review()` should only create a review when `profile_id` belongs to
`user_id` (i.e. `Profile.user_id == user_id`), the same way `get_review()` and
`list_reviews()` already scope their reads through `Profile.user_id`.

Actual (before fix): `create_review()` ignores `user_id` entirely and creates the review
unconditionally for any syntactically valid `profile_id`.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- `core/services/review_service.py` — `create_review()`: add the missing ownership
  check (query `Profile` scoped by `id` + `user_id` before creating the `Review`).
- `api/routes/reviews.py` — `create_review_endpoint()`: handle the new "not owned"
  result from `create_review()` and translate it into an HTTP response.
- `tests/unit/test_review_service.py` — add/extend unit tests covering the ownership
  check (owned vs. not-owned profile_id), and update existing `create_review` tests
  that didn't previously mock the new `Profile` lookup.
- Reference (read-only, pattern source): `get_review()` and `list_reviews()` in the
  same service file, which already implement the `Profile.user_id` scoping pattern.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. **Red** — add failing unit tests in `test_review_service.py` asserting
   `create_review()` returns `None` when `profile_id` isn't owned by `user_id`, and
   that it still creates a review when it is owned.
2. **Green** — implement the fix: query `Profile` with
   `select(Profile).where(and_(Profile.id == profile_id, Profile.user_id == user_id))`
   before constructing the `Review`; return `None` if no profile is found.
3. **Wire the endpoint** — in `create_review_endpoint()`, raise `HTTPException(404,
   "Profile not found")` when `create_review()` returns `None`, matching the 404
   behavior `get_review_endpoint()` already uses for cross-user access.
4. **Fix up existing tests** — update the pre-existing `create_review` tests to mock
   the new `db.execute()` call (Profile lookup) so they still exercise the "owned"
   path correctly.
5. **Verify** — run the unit suite and confirm no regressions beyond known pre-existing,
   unrelated failures in the test environment.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

- **Input:** `db` session, `profile_id: UUID`, `user_id: UUID` (the authenticated
  user's ID, already passed by the endpoint but previously discarded).
- **Output:**
  - If `Profile.id == profile_id AND Profile.user_id == user_id` matches a row:
    creates and returns the `Review` (status `"pending"`), same as before.
  - If no match: returns `None`, no `Review` row is created, no DB write occurs.
  - At the API layer: `POST /reviews` returns `404 Not Found` (`"Profile not found"`)
    instead of `200 OK` when the profile isn't owned by the caller.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- **Behavior change risk:** any existing client code/tests that assumed
  `create_review()` always succeeds for a syntactically valid `profile_id` will need
  to handle the new `None` / 404 case.
- **Test environment quirk:** several pre-existing unit tests in
  `test_review_service.py` (`get_review`/`list_reviews`) fail on this environment due
  to an unrelated `AsyncMock` vs `Mock` mismatch when mocking `Result.scalars()`
  (confirmed via `git stash` baseline, not introduced by this fix). Worth flagging
  separately rather than silently working around in this change.
- **Response code choice:** used 404 (not 403) for consistency with `get_review()`'s
  existing behavior of not revealing whether a `profile_id` exists for another user —
  worth confirming this is still the desired security posture for `create`, not just
  `read`.

### Edge cases
What inputs or states should your fix handle gracefully?

- `profile_id` doesn't exist at all (no row in `profiles`) → same `None`/404 outcome
  as a profile that exists but belongs to someone else (no distinction leaked).
- `profile_id` belongs to the authenticated user → unaffected, review is created as
  before.
- Malformed/non-UUID `profile_id` → already rejected upstream by FastAPI/Pydantic
  validation on `ReviewCreate.profile_id: UUID` before reaching the service.
- Authenticated user has zero profiles → any `profile_id` they supply fails the
  ownership check and returns 404, same as the "wrong owner" case.
