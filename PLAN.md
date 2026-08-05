## Solution plan

**Issue:** [Review creation does not verify profile ownership](https://github.com/ascherj/pathreview/issues/163)

### Understand

`POST /reviews` correctly passes both `data.profile_id` and the authenticated
user's ID to `core.services.review_service.create_review()`. However,
`create_review()` never uses `user_id`: it constructs and commits a `Review`
using only the caller-supplied profile ID. An authenticated user who learns
another user's profile UUID can therefore create a review for that profile and
start background processing.

The expected behavior is that review creation succeeds only when a `Profile`
matches both the requested `profile_id` and the current `user_id`. A missing or
unowned profile should produce the same not-found response so the API does not
reveal whether another user's profile exists. No review should be committed and
no background task should be scheduled when the ownership check fails.

The reproduction in
`tests/unit/test_review_service.py::TestReviewService::test_create_review_rejects_profile_not_owned_by_user`
fails because `create_review()` performs zero database queries before inserting
the review.

### Map

Files and functions involved:

- `core/services/review_service.py`
  - `create_review()` is the root cause and needs an ownership-scoped `Profile`
    lookup before constructing a `Review`.
  - `get_review()` and `list_reviews()` provide existing examples of scoping
    review access with `Profile.user_id`.
- `core/services/profile_service.py`
  - `get_profile()` is the existing ownership-query pattern to follow and
    establishes the service convention of returning `None` for missing or
    unowned profiles.
- `api/routes/reviews.py`
  - `create_review_endpoint()` must convert a `None` service result into a 404
    and must not call `background_tasks.add_task()` on rejection.
- `tests/unit/test_review_service.py`
  - Extend the reproduction into regression coverage for owner, non-owner, and
    nonexistent-profile cases.
- `tests/unit/test_review_routes.py` (new)
  - Add focused endpoint tests for the 404 response and background-task
    behavior.

No model or migration file should change because the ownership relationship
already exists in `core/models/profile.py`.

### Plan

1. Update `create_review()` to select a `Profile` with both
   `Profile.id == profile_id` and `Profile.user_id == user_id` before creating a
   review.
2. Return `None` without adding or committing a `Review` when that
   ownership-scoped query finds no profile, and update the function's return
   annotation and docstring to make the contract explicit.
3. Update `create_review_endpoint()` to raise a generic 404 `"Profile not
   found"` when the service returns `None`, before scheduling `process_review`.
4. Expand `tests/unit/test_review_service.py` to verify that the owner succeeds,
   a different user is rejected, a nonexistent profile is rejected, and rejected
   requests cause no database write.
5. Add route-level tests in `tests/unit/test_review_routes.py` confirming that
   rejected profile IDs return 404 and do not enqueue background processing,
   while an owned profile still returns a pending review and schedules one task.

### Inputs & outputs

The service takes an async database session, the requested profile UUID, and the
authenticated user's UUID. On an ownership match it should produce the existing
pending `Review`, commit it, refresh it, and allow the endpoint to enqueue
processing. On no match it should return `None`, perform no insert or commit,
and cause the endpoint to return HTTP 404 without a background task.

The public request and successful `ReviewResponse` schema remain unchanged.

### Risks & unknowns

- `api/routes/reviews.py` currently expects `create_review()` to always return a
  `Review`; the `None` check must occur before reading `review.id` or validating
  the response.
- Returning 403 would confirm that a profile exists but belongs to someone else.
  The plan uses one ownership-scoped query and a generic 404, matching the
  behavior in `api/routes/profiles.py`, to avoid that information leak.
- Unit mocks can prove query and write behavior but cannot prove the database
  enforces the full relationship. If the integration-test setup is available,
  add or run an API test with two persisted users and profiles.
- The endpoint passes its request-scoped database session into
  `BackgroundTasks`. That lifecycle concern is outside issue #163; tests should
  verify only that unauthorized requests do not schedule the existing task.

### Edge cases

- The profile UUID exists and belongs to the authenticated user: create exactly
  one pending review.
- The profile UUID exists but belongs to a different user: return 404, with no
  review insert, commit, or background task.
- The profile UUID does not exist: return the same 404 and avoid revealing any
  ownership information.
- The UUID is malformed: preserve FastAPI/Pydantic's existing validation error
  rather than reaching the service.
- The ownership query raises a database error: preserve the endpoint's existing
  rollback and generic 500 behavior.
- Concurrent valid requests for the same owned profile: do not introduce a new
  uniqueness restriction unless product requirements specify one.
