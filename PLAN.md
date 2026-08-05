## Solution plan

**Issue:** [#163 - Review creation does not verify profile ownership](https://github.com/ascherj/pathreview/issues/163)

### Understand

**Root cause:** The `POST /reviews` endpoint accepts an authenticated user's request but doesn't verify that the profile belongs to that user. An attacker can create reviews on any profile by supplying another user's profile ID in the request.

**Expected behavior:** Only the owner of a profile should be able to create reviews for that profile.

**Actual behavior:** Any authenticated user can create a review for any profile, regardless of ownership.

**Comparison with other endpoints:**
- `get_review()` joins with Profile and filters by `Profile.user_id == user_id` ✓
- `list_reviews()` joins with Profile and filters by `Profile.user_id == user_id` ✓
- `create_review()` accepts profile_id without ownership verification ✗

### Map

**Files to touch:**
1. `core/services/review_service.py` - Update `create_review()` function to verify ownership
2. `api/routes/reviews.py` - Update `create_review_endpoint()` to handle ownership check or raise 403
3. `tests/unit/test_review_service.py` - Add test documenting the vulnerability (already added)

### Plan

**Sub-tasks:**

1. **Add ownership check to `create_review()` service**
   - Modify `create_review()` to accept `user_id` parameter (already does)
   - Query Profile by id and verify `profile.user_id == user_id`
   - Return None if ownership verification fails (or raise appropriate exception)
   - Match the pattern used in `get_review()` with SQL join and filter

2. **Update `create_review_endpoint()` to handle verification failure**
   - Check if `create_review()` returns None (indicating ownership check failed)
   - Raise `HTTPException(status_code=403, detail="Cannot create review on this profile")`
   - Ensure error is logged appropriately

3. **Test the fix**
   - Verify test `test_create_review_missing_ownership_check()` now fails/passes appropriately
   - Confirm that create_review with wrong user_id returns None
   - Confirm endpoint returns 403 when profile doesn't belong to user

### Inputs & outputs

**Input:** `POST /reviews` with `profile_id` in request body from authenticated user

**Output:** 
- Success (201): Review created if `profile_id` belongs to current user
- Forbidden (403): Error response if `profile_id` belongs to different user

### Risks & unknowns

1. **Risk: Cascade behavior** - Deleting a profile cascades to reviews; ensure cascade still works after ownership check
2. **Risk: Background task** - `process_review()` background task doesn't verify ownership; may need to add check there too
3. **Unknown: Transaction isolation** - Profile could be deleted between ownership check and review creation; SQL should handle this

### Edge cases

1. **Non-existent profile** - User supplies valid UUID for profile that doesn't exist → 403 or 404?
2. **Deleted profile** - Profile was deleted after user obtained ID → cascading delete handles it
3. **Concurrent requests** - Multiple requests creating reviews simultaneously on same profile → should all succeed if user owns profile
4. **User_id mismatch** - Endpoint receives profile_id and current_user.id, but are they the same type? Check UUID handling
