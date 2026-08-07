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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I updated `create_review()` to look up the requested profile using both the
profile ID and the authenticated user's ID. The service now returns `None`
instead of creating a review when the profile is missing or belongs to another
user, and I added unit tests for authorized and unauthorized review creation.

**Next steps:**
Update the `POST /reviews` route to return `404 Not Found` when the service
rejects the profile, confirm that no background task is started in that case,
and run the focused tests and project-wide checks.

**Blockers:**
The repository's full test and code-quality commands have existing unrelated
failures. I recorded the baseline results so I could confirm that my changes do
not introduce new failures.

---

### Check-in 2 (end of week)

**PR link:** [Pull request #996](https://github.com/ascherj/pathreview/pull/996)

**Branch:** `fix/163-enforce-profile-ownership-on-review-creation`

**What you built:**
Review creation now verifies that the supplied profile belongs to the
authenticated user. Requests for a missing or unowned profile receive a
`404 Not Found` response, no review is written, and no review-processing
background task is scheduled.

**Tests added or updated:**
I added service tests for owned and unowned profiles, route tests for the
success and rejection paths, and updated the existing review service fixture
to return an owned profile. All four focused ownership and route tests pass. A
manual API check also confirmed that a user cannot create a review using a
second user's profile UUID and that the review count does not change.

**Self-review confirmation:** [X] `make check` passes*  [X] `make test-unit`
passes*

\*Under the course's pre-existing-failure policy, these boxes mean the change
introduces no new failures. All four issue-specific tests pass; the full
commands retain the unrelated failures recorded before implementation.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No review came in

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]
N/A

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
Couple of things were actually harder than I expected. First and foremost, was trying to reproduce the issue such with two different users. I had to understand how authentication works, obtain the correct profile UUIDs, and trace the request through the route and service. 
It was also challenging to separate failures caused by my changes from the repository’s existing set of test and formatting failures.



**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
I learned that instead of trying to understand the entire project at once, its better to focus on smaller aspect and continue from there. I learn how to trace one request at a time through the route, service, database model, and tests instead of trying to understand the entire project at once. 
I also learned the importance of following existing patterns, testing side effects with changes, and recording baseline failures before making changes can be useful.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
AI tools helped me navigate this unfamiliar codebase such as tracing the request from the API route to the service and database models, and understand the project’s testing conventions. They also helped me reproduce the issue once I figured out whats going on, understand and write test matching the testing convention , and interpret unrelated failures from the full test suite. 
However, AI-generated suggestions still needed careful review because they did not always match the project’s conventions. They did not recognize which failures already existed.


**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I would run the full tests and quality checks before changing anything and save the baseline results immediately.
I would also inspect the existing test files and contribution guide earlier, then build the fix in smaller steps: reproduce the bug, update the service, update the route, and test each step.

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I am most proud that I was able to navigate through unfamiliar codebase with help of AI and able to understand and reproduce a authorization issue that can happen in real world and implemented a focused fix along with tests that follows the project’s architecture. 