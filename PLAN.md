## Solution plan

**Issue:** [IDOR vulnerability in POST /reviews endpoint](https://github.com/ascherj/pathreview/issues/XYZ)

Authenticated users can create reviews for other users' profiles by passing an arbitrary `profile_id`.

---

### Understand

**Root cause:**
The `create_review()` function in `core/services/review_service.py` receives a `user_id` parameter but ignores it entirely. It creates a Review record for any supplied `profile_id` without validating that the profile belongs to the authenticated user.

**Expected behavior:**
- User A should only be able to create reviews for profiles that belong to User A
- If User A attempts to create a review for User B's profile, the API should reject the request (403 Forbidden or 404 Not Found)

**Actual behavior:**
- User A can create reviews for any profile in the system, including profiles owned by User B
- The review is created successfully and appears in User A's review history

**Why it matters:**
This is an Insecure Direct Object Reference (IDOR) vulnerability. The read endpoints (`get_review()` and `list_reviews()`) already correctly scope reviews by checking `Profile.user_id == user_id`, but the write endpoint (`create_review()`) bypasses this check entirely. This inconsistency enables unauthorized write access.

---

### Map

**Files involved:**

- **`api/routes/reviews.py`** (lines 22-60)
  - `create_review_endpoint()`: Receives authenticated user and passes `user_id` to service

- **`core/services/review_service.py`** (lines 9-24)
  - `create_review()`: Creates Review record **without validating profile ownership**
  - `get_review()` (lines 27-39): Reference implementation — correctly scopes by `Profile.user_id`
  - `list_reviews()` (lines 42-64): Reference implementation — correctly scopes by `Profile.user_id`

- **`core/models/profile.py`** (line 13)
  - Profile model: Has `user_id` field linking to owner

- **`core/models/review.py`** 
  - Review model: Has `profile_id` and `status` fields

---

### Plan

1. **Update `create_review()` to verify profile ownership**
   - Before creating the Review, query the Profile table
   - Check that `Profile.id == profile_id` AND `Profile.user_id == user_id`
   - If profile doesn't exist or doesn't belong to user, raise `HTTPException(404)` to avoid leaking profile existence

2. **Add authorization check inline with existing query pattern**
   - Use the same `.join(Profile).where(...)` pattern as `get_review()` and `list_reviews()`
   - Keep logic inside the service function (not the route) to maintain consistency

3. **Add unit tests for the authorization check**
   - Test that a user can create a review for their own profile (happy path)
   - Test that a user cannot create a review for another user's profile (authorization failure)
   - Test that creating a review for a non-existent profile returns 404

4. **Verify no other code paths bypass the fix**
   - Search for other calls to `create_review()` to ensure they're all protected
   - Check if `process_review()` background task needs similar validation

5. **Test locally to confirm vulnerability is fixed**
   - Reproduce the original IDOR attack from JOURNAL.md
   - Verify it now returns 404 instead of creating the review

---

### Inputs & outputs

**Function signature:**
```python
async def create_review(
    db,
    profile_id: UUID,
    user_id: UUID,
) -> Review:
```

**Expected behavior after fix:**

| Scenario | Input | Output |
|----------|-------|--------|
| User creates review for own profile | `profile_id=user_a_profile`, `user_id=user_a` | Creates Review, returns 201 |
| User creates review for another's profile | `profile_id=user_b_profile`, `user_id=user_a` | Raises HTTPException(404) |
| User creates review for non-existent profile | `profile_id=fake-uuid`, `user_id=user_a` | Raises HTTPException(404) |

---

### Risks & unknowns

**Known risks:**

- **Return code ambiguity:** Should we return 404 or 403 for "profile belongs to another user"?
  - 404 hides the existence of the profile (more secure, prevents enumeration attacks)
  - 403 is semantically correct but leaks that the profile exists
  - **Decision:** Use 404 to match security best practice

- **Background task validation:** The `process_review()` background task receives a `profile_id` but doesn't validate ownership
  - Currently it just fetches the profile without checking user context
  - This is acceptable (background task has DB access) but worth documenting

**Unknowns:**

- Are there integration tests that expect the old (vulnerable) behavior?
- Does any client code rely on the ability to create reviews cross-user?

---

### Edge cases

1. **Null or missing values:**
   - `profile_id=None` → FastAPI validation catches before reaching service
   - `user_id=None` → Auth middleware catches before reaching route

2. **Profile lifecycle:**
   - Profile deleted but review exists → Works (cascade deletes reviews anyway)
   - Profile created after this fix → Works (new profiles will have user_id set)

3. **Concurrent requests:**
   - User A and User B both create reviews simultaneously for different profiles → No conflict
   - Race condition between profile deletion and review creation → DB constraints handle (foreign key error becomes 500)

4. **Malformed IDs:**
   - Invalid UUID format in `profile_id` → FastAPI validation rejects
   - Valid UUID but profile doesn't exist → 404 from our new check

5. **Authorization edge case:**
   - User with suspended account → Auth middleware rejects (not this function's concern)
   - User token expired mid-request → Auth middleware catches

---

## Implementation checklist

- [ ] Modify `create_review()` to query and validate profile ownership
- [ ] Ensure consistent error handling (404 for any authorization failure)
- [ ] Write unit tests for happy path and auth failures
- [ ] Search codebase for other `create_review()` calls
- [ ] Test locally with original exploit from JOURNAL.md
- [ ] Verify read endpoints still work correctly
- [ ] Update this PLAN.md after implementation if needed
