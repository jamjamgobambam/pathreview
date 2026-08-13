# Solution plan

**Issue:** [#163 — Review creation does not verify profile ownership](https://github.com/ascherj/pathreview/issues/163)

### Understand

The `POST /reviews` endpoint passes both the requested `profile_id` and the authenticated user's `user_id` to `create_review()`. However, `create_review()` currently uses the `profile_id` to create the review without checking whether that profile belongs to the authenticated user. This means a user who knows another user's profile UUID could potentially create a review for that profile.

The expected behavior is that a review should only be created when the requested profile belongs to the authenticated user. If the profile does not exist or belongs to another user, review creation should be rejected before anything is added to the database.

I reproduced the issue with a unit test that supplies a profile owned by a different user. The test fails because `create_review()` still calls `db.add()` and creates the review.

### Map

The main files involved are:

* `api/routes/reviews.py` — handles `POST /reviews`, gets the authenticated user, and passes `current_user.id` to the service.
* `core/services/review_service.py` — contains `create_review()`, where the ownership validation is currently missing.
* `tests/unit/test_review_service.py` — contains the review service tests and will contain coverage for the cross-user ownership case.

The existing `get_review()` and `list_reviews()` functions in `core/services/review_service.py` already use `Profile.user_id` to scope review access to the authenticated user. I can use these functions as references for how ownership is handled elsewhere in the service.

### Plan

1. Update `create_review()` in `core/services/review_service.py` to query for the requested profile and verify that its `user_id` matches the authenticated `user_id`.
2. If the profile does not exist or is not owned by the current user, stop review creation before calling `db.add()` or committing a review.
3. Preserve the existing review creation behavior for profiles that are owned by the authenticated user, including the initial `"pending"` status.
4. Update `tests/unit/test_review_service.py` so the cross-user case verifies that unauthorized review creation is rejected.
5. Add or update test coverage for the valid-owner case and run the targeted review service tests to confirm the ownership check works without breaking normal review creation.

### Inputs & outputs

**Inputs:**

* `profile_id` — UUID of the profile that the user wants reviewed.
* `user_id` — UUID of the currently authenticated user.
* Database session used to look up the profile and create the review.

**Expected output for a valid profile:**

* A new `Review` associated with the requested profile.
* The review begins with a `"pending"` status and is committed to the database.

**Expected output for an unauthorized or unavailable profile:**

* Review creation is rejected.
* No `Review` is added or committed to the database.
* The API should return an appropriate error rather than creating a review.

### Risks & unknowns

One decision I need to confirm is which error response the project expects when the profile does not exist or belongs to another user. The existing read endpoints use a `404 Not Found` response when a review cannot be accessed by the current user, so I will investigate whether review creation should follow the same pattern.

There are also existing unrelated failures in `tests/unit/test_review_service.py` involving the setup of `AsyncMock` results. I will keep the Issue #163 tests targeted so those existing failures are not confused with failures caused by my ownership change.

I also need to make sure the ownership validation happens before the review is added or committed so an unauthorized request cannot leave database changes behind.

### Edge cases

* The profile exists and belongs to the authenticated user — review creation should succeed normally.
* The profile exists but belongs to another user — review creation should be rejected.
* The supplied `profile_id` does not match any profile — review creation should be rejected.
* A valid UUID is supplied for a profile that the current user cannot access — it should not reveal or create data for that profile.
* The ownership check succeeds but a later database operation fails — existing error handling and rollback behavior should continue to work.
