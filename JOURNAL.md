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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Reproduction test](https://github.com/saimantmg01/pathreview/commit/ec8893e0f1c4ac2f729973f47195a378a20dbd2f)

**Reproduction summary:**
I authenticated as `user1@example.com` and submitted `user2@example.com`'s
profile UUID to `POST /reviews`; the endpoint returned `200 OK` and created a
pending review instead of rejecting the cross-user request. I also reproduced
the root cause with a focused unit test showing that `create_review()` returns
a newly constructed review without executing an ownership query.

**PLAN.md link:** [PLAN.md](https://github.com/saimantmg01/pathreview/blob/fix/163-enforce-profile-ownership-on-review-creation/PLAN.md)

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
Confirm whether maintainers prefer `404 Not Found` or `403 Forbidden` for a
profile owned by another user; the current codebase consistently uses `404` to
avoid disclosing resource existence.
