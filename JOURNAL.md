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

**Commit:** https://github.com/ascherj/pathreview/commit/2235af1

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/2235af1

**Reproduction summary:**
I reproduced the IDOR vulnerability by authenticating as one user, retrieving another user's profile ID from the database, and sending a `POST /reviews` request with that profile ID. The API accepted the request and created a review for the other user's profile (HTTP 200), confirming that the endpoint does not validate profile ownership despite receiving the authenticated user's ID.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
- Should the endpoint return 403 Forbidden or 404 Not Found when a user tries to create a review for another user's profile? (Decision: 404 to avoid enumeration attacks, matching security best practice)
- Need to verify whether the background task `process_review()` requires similar ownership validation or if DB context is sufficient
- Should check if any integration tests or client code depends on the current (vulnerable) cross-user review creation behavior

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

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the ownership validation in `create_review()` so reviews can only be created for profiles that belong to the authenticated user. I also added regression tests covering both the happy path and the unauthorized cross-user case.

**Next steps:**
I’m finalizing verification and preparing the PR description with the reproduction summary and evidence from the test run.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [pending submission]

**Branch:** `fix/152-faithfulness-short-claims`

**What you built:**
I fixed the IDOR vulnerability in the review creation flow by enforcing that `create_review()` only accepts profiles owned by the authenticated user. This prevents a logged-in user from creating reviews for another user’s profile by supplying an arbitrary `profile_id`.

**Tests added or updated:**
I updated `tests/unit/test_review_service.py` to add a regression test for unauthorized review creation and to ensure the existing review service behavior remains covered.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review feedback received by the end of the week.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Understanding the codebase structure was more challenging than I anticipated. The project has many interconnected files and components, and I had to trace dependencies across the `core/services/`, `api/routes/`, and test directories to fully understand where the vulnerability existed and how my fix would affect the system. Writing tests that covered both the happy path and edge cases—like ensuring that `create_review()` correctly rejects cross-user requests—required careful thought about what scenarios to test. Fixing the edge case where the ownership validation needed to integrate cleanly with existing error handling was also trickier than expected.

**What did you learn about working in a large codebase?**
I learned that large codebases are deeply interconnected—every component depends on others toward a common goal. This means that even a small change (like adding ownership validation) can have ripple effects across tests, error handling, and possibly other services. I realized that changing just one line or one function signature could inadvertently break the entire system if I didn't understand the full dependency chain. It reinforced the importance of reading related code carefully, tracing how data flows through services and routes, and writing regression tests to catch unintended side effects.

**How did AI tools help — and where did they fall short?**
AI was most helpful for understanding the overall codebase structure and breaking down what the vulnerability was. It helped me navigate the files, understand the problem statement, and think through the solution approach. However, AI tools struggled with the nuanced decision-making required to actually solve the problem—like deciding whether to return 404 vs 403, understanding the security implications of each choice, and ensuring my fix didn't break existing workflows. I had to research security best practices and trace the code flow myself to make those decisions confidently.

**What would you do differently if you started over?**
I would spend more time on issue selection and planning upfront. Looking back, I'd want to choose an issue that gave me clearer scope boundaries or one where the fix was more straightforward. I'd also plan out the entire solution—including all the tests and edge cases—before diving into the code. This would have reduced the back-and-forth of discovering new dependencies or realizing I needed to handle edge cases I hadn't anticipated.

**What are you most proud of from this module?**
I'm proud that I was able to complete the full contribution cycle from issue selection through PR submission. Despite the complexity of the codebase and the challenges understanding all the moving parts, I successfully identified a real security vulnerability, reproduced it, fixed it, added proper tests, and followed best practices in submitting my work. The fact that I persisted through the confusion of understanding a large unfamiliar codebase and delivered a working fix is something I can point to.
