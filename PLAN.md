## Solution plan

**Issue:** [Review creation does not verify profile ownership
(#163)](https://github.com/ascherj/pathreview/issues/163)

### Understand

When a user sends `POST /reviews`, the route passes two IDs to
`create_review()`:

- The profile ID from the request.
- The ID of the logged-in user.

The service ignores the logged-in user's ID. It creates a review as long as the
profile ID exists, even if that profile belongs to someone else.

The service should first check that the profile belongs to the logged-in user.
If it does, the review should be created normally. If it does not, the request
should return `404 Not Found` and no review should be created.

### Map

Files I expect to change:

- `core/services/review_service.py`
  - Check profile ownership inside `create_review()`.
  - Return `None` when the profile is missing or belongs to another user.
- `api/routes/reviews.py`
  - Return `404 Not Found` when `create_review()` returns `None`.
  - Only start the background review task after a review is created.
- `tests/unit/test_review_ownership.py`
  - Test owned, unowned, and missing profiles.
  - Confirm that rejected requests do not write to the database.
- `tests/unit/test_review_routes.py` (new)
  - Test the route's `404` response.
  - Confirm that rejected requests do not start a background task.


### Plan

1. In `create_review()`, query for a profile whose `id` matches the requested
   profile ID and whose `user_id` matches the logged-in user.
2. If no matching profile is found, return `None` before creating or saving a
   review.
3. Update the route to turn that `None` result into `404 Not Found`. Add the
   background task only when review creation succeeds.
4. Add tests for allowed and rejected requests. Run the unit tests, linting,
   type checks, and the manual two-user reproduction.

### Inputs & outputs

Inputs:

- A database session.
- The requested profile UUID.
- The logged-in user's UUID.

Expected results:

- The profile belongs to the user: create a pending review and return
  `200 OK`.
- The profile belongs to someone else: create nothing and return
  `404 Not Found`.
- The profile does not exist: create nothing and return `404 Not Found`.
- The profile ID is not a valid UUID: keep FastAPI's existing
  `422 Unprocessable Entity` response.

### Risks & unknowns

- The issue does not say whether to return `403` or `404`. Other PathReview
  routes use `404` for resources that are missing or owned by someone else, so
  I plan to follow that pattern.
- Existing review service tests may need updated mocks because
  `create_review()` will now run a profile query before creating a review.
- Profile IDs are stored as strings in the models but arrive as UUID objects.
  Existing queries already work this way, but the tests should confirm it.

### Edge cases

- The user submits their own profile ID.
- The user submits another user's profile ID.
- The user submits a valid UUID that does not match any profile.
- The user submits an invalid UUID.
- A rejected request must not add, commit, or refresh a review.
- A rejected request must not start background review processing.
- A database error should still use the route's existing rollback and
  `500 Internal Server Error` handling.
