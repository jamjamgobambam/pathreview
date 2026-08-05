# PLAN.md

## Issue #163 — Review creation does not verify profile ownership

### Problem

`create_review()` in [core/services/review_service.py](core/services/review_service.py)
accepts a `user_id` argument but never uses it. It builds a `Review` straight
from the caller-supplied `profile_id` with no check that the profile belongs
to the authenticated user. `get_review()` and `list_reviews()` in the same
file correctly scope every query through `Profile.user_id` — `create_review()`
is the odd one out.

### Reproduction

See [tests/integration/test_review_ownership.py](tests/integration/test_review_ownership.py).
Register User A and User B, have User B create a profile, then have User A
call `POST /reviews` with User B's `profile_id`. Expected: 403/404. Actual:
200, and a `pending` review is created against User B's profile.

### Files to change

- `core/services/review_service.py` — add the ownership check inside
  `create_review()`.
- `api/routes/reviews.py` — translate a "not owned" result into the correct
  HTTP status in `create_review_endpoint()`.
- `tests/integration/test_review_ownership.py` — already added (reproduction
  test); should flip from failing to passing once the fix lands.
- `tests/unit/test_review_service.py` — extend with a unit-level ownership
  test for `create_review()`.

### Sub-tasks (in order)

1. **Reuse the existing ownership-scoped lookup.**
   `core/services/profile_service.py` already has
   `get_profile(db, profile_id, user_id)`, which selects
   `Profile` filtered on `(Profile.id == profile_id) & (Profile.user_id ==
   user_id)` and returns `None` if it doesn't match. Import and call this
   from `create_review()` instead of writing a new query — no duplicated
   ownership logic.
2. **Check the result.** If `get_profile(...)` returns `None`, do not create
   the review.
3. **Signal the failure to the route layer.** `create_review()` raises an
   `HTTPException(404, ...)` directly, mirroring how `get_review_endpoint`
   and `get_profile_endpoint` already raise 404 for "not found or not
   owned." Keeps the pattern consistent across the codebase rather than
   introducing a new return-`None`-and-check-in-the-route convention.
4. **Choose 403 vs 404.** Use `404 Not Found` rather than `403 Forbidden` —
   returning 403 confirms to an attacker that a profile with that ID exists,
   which leaks information. 404 matches what `get_review`/`get_profile`
   already return for "not yours," so it's also the more consistent choice.
5. **Update `api/routes/reviews.py`** so `create_review_endpoint()` surfaces
   the 404 correctly (matching the existing try/except shape already used in
   that file).
6. **Confirm the reproduction test passes.** Re-run
   `tests/integration/test_review_ownership.py` — it should now get 404
   instead of 200.
7. **Add a unit test** for `create_review()` covering the cross-user case
   with a mocked DB session, consistent with the existing style in
   `tests/unit/test_review_service.py`.
8. **Run the full check suite** — `make check && make test-unit
   test-integration` — before opening the PR in Week 9.

### Risks / edge cases

- **Extra DB query cost.** The fix adds one `SELECT` on `Profile` per review
  creation. Negligible, but worth calling out since `create_review()`
  currently does zero reads.
- **404 vs 403 information leak.** Covered above — going with 404 to avoid
  confirming profile existence to non-owners.
- **Profile genuinely doesn't exist vs. profile exists but isn't the
  caller's.** Both cases should return the same 404 response, so a caller
  can't distinguish "no such profile" from "not your profile."
- **Existing passing tests may assume no ownership check.** The unit tests in
  `tests/unit/test_review_service.py` (e.g.
  `test_create_review_calls_db_add`) call `create_review()` with unrelated
  random `profile_id`/`user_id` pairs and expect it to succeed — once the
  ownership check is added, those mocks will need a `Profile` lookup mocked
  in too, or they'll break.
- **Background processing (`process_review`) is unaffected** — it already
  operates purely on `profile_id` after the review row exists, so no change
  needed there; the fix only has to stop the review from being created in
  the first place.
- **Consistency with `profile_service.py`** — confirmed:
  `profile_service.get_profile()` is the reusable ownership-scoped lookup;
  reuse it rather than duplicating the query in `review_service.py`.
