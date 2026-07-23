## Week 7 — Issue selection

**Issue link:** [Issue #163](https://github.com/ascherj/pathreview/issues/163)

**Issue title:** Review creation does not verify profile ownership

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The `POST /reviews` endpoint passes the authenticated user's ID to
`create_review()`, but `core/services/review_service.py` currently ignores that
argument. This allows a review to be created from a supplied `profile_id`
without confirming that the profile belongs to the authenticated user. A
successful fix will enforce profile ownership during review creation, making
the endpoint consistent with the ownership checks already used when reviews
are retrieved or listed.

**Branch name:** fix/163-enforce-profile-ownership-on-review-creation

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger
