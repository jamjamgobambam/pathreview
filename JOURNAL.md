## Reproduction: POST /reviews IDOR vulnerability

**Issue description:** Authentication bypass in review creation endpoint

**Problem:**
The `POST /reviews` endpoint accepts a `profile_id` parameter but does not validate that the authenticated user owns the profile. This allows any authenticated user to create reviews for other users' profiles.

**Steps to reproduce:**

1. **Get your auth token:**
   - Open browser console (F12)
   - Run: `localStorage.getItem('token')` or check Network tab for Bearer token

2. **Get two different profile IDs:**
   - Run in terminal: `python -c "..."`  (query script above)
   - Note one profile ID that belongs to the current user
   - Note a different profile ID belonging to another user

3. **Exploit the vulnerability in browser console:**
   ```javascript
   fetch('http://localhost:8000/reviews', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'Authorization': 'Bearer YOUR_TOKEN'
     },
     body: JSON.stringify({profile_id: 'OTHER_USERS_PROFILE_ID'})
   }).then(r => r.json()).then(console.log)
   ```

4. **Expected result (vulnerable):**
   - API returns 200 OK with new review object
   - Review is created for the other user's profile

5. **Actual result:**
   - ✓ CONFIRMED VULNERABLE: Received `{id: '97011efa...', profile_id: '51c47844-b860...', status: 'pending', ...}`
   - Successfully created a review for a profile not owned by authenticated user

**Root cause:**
- [core/services/review_service.py](core/services/review_service.py#L8-L20): `create_review()` function ignores the `user_id` parameter
- Does not validate that `Profile.user_id == user_id` before creating the review
- Contrast: `get_review()` and `list_reviews()` correctly scope by `Profile.user_id`

**Impact:**
- Any authenticated user can create reviews for any other user's profile
- Breaks the access control pattern established by read endpoints
- IDOR (Insecure Direct Object Reference) vulnerability

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The FaithfulnessChecker in rag/evaluator/faithfulness_checker.py scores
generated feedback claims against retrieved context, but short factual
claims (e.g. "Knows Python") could never be marked as supported even
when the context fully backed them up. Tracing the failing tests showed
three compounding causes: tokenization didn't strip punctuation (so
"python," never matched "python"), the overlap threshold was a flat
"2+ tokens must match" rule that a 2-token claim could never satisfy,
and per-claim scoring was all-or-nothing, so a compound sentence with
one true and one false fact could only score 0 or 1, never a middle
value. A successful fix makes the checker give proportional credit
based on how much of a claim's meaningful content is present in the
context, in rag/evaluator/faithfulness_checker.py.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger