## Solution plan

**Issue:** Review creation does not verify profile ownership — https://github.com/ascherj/pathreview/issues/163

### Understand

The root cause is that `POST /reviews` accepts a `profile_id` from the request body and passes the authenticated user's id into `create_review()`, but `create_review()` does not actually use `user_id` to verify profile ownership.

Expected behavior: a user should only be able to create a review for a profile they own. If the profile does not exist or belongs to another user, the API should reject the request.

Actual behavior: `core/services/review_service.py` creates a `Review` for any valid `profile_id`, even if that profile belongs to a different user. This means a user who knows another user's profile UUID could create a review tied to that profile.

### Map

Files involved:

- `api/routes/reviews.py` — defines `POST /reviews` and passes `profile_id` plus `current_user.id` into the review service.
- `core/services/review_service.py` — contains `create_review()`, where ownership validation is missing.
- `core/services/profile_service.py` — already has the correct ownership-checking pattern in `get_profile()`.
- `core/models/profile.py` — defines `Profile.user_id`, which identifies profile ownership.
- `core/models/review.py` — defines `Review.profile_id`, which links reviews to profiles.
- `tests/unit/test_review_service.py` — existing review service tests; this is where I should add tests for authorized and unauthorized review creation.

Expected files to touch:

- `core/services/review_service.py`
- `tests/unit/test_review_service.py`
- Possibly `api/routes/reviews.py` if the route needs to translate an unauthorized service result into a `404` or `403`.

### Plan

1. Add a failing test in `tests/unit/test_review_service.py` proving that `create_review()` should not create a review when the requested profile belongs to another user.
2. Update `create_review()` in `core/services/review_service.py` to query `Profile` using both `Profile.id == profile_id` and `Profile.user_id == user_id` before creating the review.
3. If no matching profile is found, return `None` or raise an `HTTPException`, then make sure `POST /reviews` responds with an appropriate error instead of creating a review.
4. Preserve the normal success path: when the authenticated user owns the profile, create a review with `status="pending"`, `sections=None`, and `overall_score=None`.
5. Run the review service tests and any related API tests to confirm the unauthorized case fails before the fix and passes after the fix.

### Inputs & outputs

Input: a `POST /reviews` request body containing a `profile_id`, plus the authenticated user's JWT-derived `current_user.id`.

Output after the fix:

- If the profile belongs to the authenticated user, the API creates and returns a pending review.
- If the profile does not exist or belongs to another user, the API rejects the request and does not insert a review.
- Existing review retrieval and review listing behavior should remain unchanged.

### Risks & unknowns

- I need to decide whether unauthorized review creation should return `404 Not Found` or `403 Forbidden`. Existing profile and review lookup endpoints use `404` when a resource is missing or not owned by the current user, so `404` is probably the most consistent choice.
- If `create_review()` raises `HTTPException`, that adds API-layer behavior to the service layer. Returning `None` may keep the service cleaner, but requires the route to handle the failure.
- The background task in `api/routes/reviews.py` should only be scheduled after ownership is confirmed and the review is created.
- Existing tests in `tests/unit/test_review_service.py` use mocks heavily, so I may need to carefully mock the profile ownership query.

### Edge cases

The fix should handle:

- A valid profile owned by the authenticated user.
- A valid profile owned by a different user.
- A nonexistent `profile_id`.
- A malformed `profile_id`, which should still be handled by the existing Pydantic UUID validation.
- The background processing task should not run when review creation is rejected.
