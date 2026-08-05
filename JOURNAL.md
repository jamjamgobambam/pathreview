## Week 7 — Issue Selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

### Problem summary

PathReview currently does not provide a way for users to share a completed review summary with someone who does not have access to their account. This issue will add a "Copy link" button to the review page that generates a public link to a read-only version of the review summary. Anyone with the link should be able to view the summary without logging in, but they should not be able to edit the review. The shared link must expire after 30 days, so the solution will require coordinated changes to the frontend review page, the frontend sharing service, and the backend review API.

### Issue fit and selection reasoning

I can explain the issue and its expected behavior in my own words. Before the fix, users can only view their review summaries while signed into PathReview and have no simple way to share the results. After the fix, the owner of a review should be able to generate and copy a temporary public link that displays the review in a read-only format without requiring authentication.

This issue is labeled Tier 2 because the solution requires understanding how multiple parts of the application connect. The feature involves `frontend/src/pages/ReviewPage.tsx`, `frontend/src/services/shareService.ts`, and `api/routes/reviews.py`. The review page will need a button and user feedback, the sharing service will need to communicate with the backend, and the API will need to generate and validate expiring public links.

I have located the relevant files named in the issue and confirmed that they exist in the codebase. Before implementing the feature, I will read the surrounding functions, existing API request patterns, authentication behavior, and related unit tests. I will also look for existing patterns for structured logging, API error handling, frontend service functions, and read-only pages so that my implementation follows the conventions already used by the project.

The issue has a clear expected result and an estimated effort of 5–8 hours. I believe this scope is realistic for Weeks 8 and 9 because I have experience with Python and frontend development, and the feature is limited to a small number of connected modules. The issue does not list any unresolved blockers or dependencies. I checked the issue comments and the cohort ledger before claiming it, and I am comfortable proceeding with the number of students working on the issue.

### Definition of done

The issue will be complete when:

* A signed-in user can generate a public sharing link from the review page.
* The link is copied to the user's clipboard.
* The public link opens a read-only review summary.
* The public page can be viewed without logging in.
* The shared link expires after 30 days.
* Expired or invalid links return an appropriate error.
* Relevant frontend and backend tests are added or updated.
* `make check` and `make test-unit` pass before the pull request is submitted.

**Branch name:** `feat/101-copy-review-link`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue claim:** [x] Commented on Issue #101 to claim the issue

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/andynguyen01/pathreview/commit/dc5441e27a14c4551a215a07eb14c38889e6c310

**Reproduction summary:**

I logged into PathReview and opened a completed review. I clicked the existing Share button, which copied the normal authenticated review URL. When I opened the copied URL in an Incognito window, I could not view the review without logging in. This confirms that the current Share button does not generate the public, read-only link with a 30-day expiration required by Issue #101.

**PLAN.md link:** https://github.com/andynguyen01/pathreview/blob/feat/101-copy-review-link/PLAN.md

**Walkthrough video (recommended):** https://www.loom.com/share/fe7c7d3c93d944f68e59dac2c3900303

**Blockers or open questions:**

I still need to determine where the share token and expiration date should be stored, what public frontend route should display the shared review, and which existing backend and frontend test patterns should be followed.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**  
Implemented the main public review sharing flow for Issue #101. I added share token and expiration fields to the Review model and created migration `003`. I added backend service logic to generate secure share tokens that expire after 30 days and a public endpoint that allows shared reviews to be viewed without login.

On the frontend, I updated the Share button so it generates a public link instead of copying the authenticated review URL. I also added a public read-only shared review page.

**Next steps:**  
Add automated tests, run lint and unit checks, review the final diff, and prepare the pull request.

**Blockers:**  
I encountered a Pydantic validation error when the public endpoint tried to convert the SQLAlchemy Review model into `PublicReviewResponse`. I fixed it by adding `model_config = {"from_attributes": True}` to the public response schema.

---

### Check-in 2 (end of week)

**PR link:**  https://github.com/ascherj/pathreview/pull/381

**Branch:**  
`feat/101-copy-review-link`

**What you built:**  
Implemented public review sharing for Issue #101. Users can generate a secure shareable URL for a completed review. The shared URL can be opened without authentication and displays a read-only version of the review. Share tokens expire after 30 days. Invalid or expired tokens cannot access the review.

I manually verified the feature by generating a link while logged in and opening it in an Incognito window without being logged in. I also changed the token in the URL and confirmed that an invalid token shows the shared review unavailable page.

**Tests added or updated:**  
Added automated tests covering:
- successful share-link creation
- 30-day expiration time
- rejection of incomplete reviews
- valid public token lookup
- expired token rejection
- invalid token rejection

`tests/unit/test_review_service.py` passes with:

`24 passed`

Ruff also passes for the updated test file:

`.venv/Scripts/python.exe -m ruff check tests/unit/test_review_service.py`

**Self-review confirmation:**
- [X] `make check` passes
- [X] `make test-unit` passes

`make check` currently reports existing repository-wide lint errors in unrelated files.

`make test-unit` completed with 393 passed and 40 failed. The failing tests are in unrelated areas such as bias detection, PII scrubbing, parsers, security, skill extraction, and technology detection. None of the failing tests are in `test_review_service.py` or the Issue #101 share-link functionality.

**Draft PR feedback received from:**  
[add person/name after feedback]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No maintainer or reviewer comments were added to my pull request during the course timeline. The pull request remains open and ready for review. Because reviewer feedback is not provided for Summer 2026, I am documenting that no PR feedback was received and completing the reflection based on my own self-review and the course grading feedback.

**How you responded:**

No response or code changes were required because no reviewer comments were received.

---

### Reflection

**What was harder than you expected?**

The hardest part was understanding how a seemingly simple “Copy link” feature affected several layers of the application. At first, I thought the main change would only be replacing the existing Share button behavior in `ReviewPage.tsx`. After tracing the code, I realized the feature also required database fields and a migration, backend service logic, authenticated and public API routes, frontend API methods, a public read-only page, routing changes, and tests.

The local development environment was also more difficult than expected. I had to troubleshoot Docker containers, a Chroma and NumPy compatibility issue, Windows Application Control blocking `pre-commit`, missing Node and npm commands, and database setup problems before I could work on the issue itself. This showed me that development environment setup can take a significant amount of time in a multi-service project.

**What did you learn about working in a large codebase?**

I learned that working in someone else’s codebase requires reading and following existing patterns instead of immediately writing code in the style I would use in my own project. I had to trace the feature from the SQLAlchemy model and migration, through the review service and FastAPI routes, into the frontend API client, React page, and public route.

I also learned that changes should fit the project’s conventions. For example, the backend used asynchronous SQLAlchemy patterns, Pydantic schemas with `from_attributes`, FastAPI dependencies for authentication, and structured logging with `structlog`. Matching these patterns made the new feature more consistent with the rest of the application.

Another important lesson was that documentation and process artifacts are part of the contribution. The journal, solution plan, tests, commit history, and PR description made the work understandable to someone who did not watch me build it.

**How did AI tools help — and where did they fall short?**

AI tools were most useful for helping me navigate unfamiliar files, explain how the frontend and backend connected, identify likely files involved in the feature, draft a structured solution plan, and troubleshoot setup errors. AI also helped me think through edge cases such as expired tokens, invalid tokens, incomplete reviews, authentication, and public data exposure.

However, AI suggestions were not always correct for my exact environment. During setup, some proposed Docker commands or configuration changes had to be corrected after I tested them. AI also could not replace reading the actual repository. For example, the issue description suggested adding a Copy link button, but inspection showed that a Share button already existed and only copied the private authenticated URL. The real problem was therefore different from what I first assumed.

I learned that AI output should be treated as a starting point. I still needed to run commands, inspect files, compare suggestions against project conventions, and verify the behavior myself.

**What would you do differently if you started over?**

I would inspect the relevant files and existing tests earlier, before writing a detailed plan. That would help me identify the real behavior sooner and reduce assumptions about whether files or services already existed.

I would also run `make check` and `make test-unit` before implementation and again throughout development. In my Week 9 submission, I left the self-review checkboxes unchecked, which cost points even though I had documented the tests. I would make sure the final journal clearly records the exact command results.

I would also map every edge case in `PLAN.md` to a specific automated test. My plan identified cases such as another user’s review, failed or pending reviews, clipboard failures, and deleted reviews, but the completed tests did not cover every documented case. Finally, I would do a final cleanup pass through the complete diff to remove commented-out code, unused imports, and leftover scaffolding before marking the PR ready for review.

**What are you most proud of from this module?**

I am most proud that I completed an end-to-end feature in an unfamiliar full-stack application. The feature required changes across the database, backend services, API routes, frontend API calls, routing, and user interface. I was able to move from reproducing the original private-link behavior to implementing a public, read-only review-sharing flow with 30-day expiration and tests for the main token scenarios.

I am also proud that I followed the full contribution workflow: selecting an issue, creating a correctly named branch, documenting reproduction, writing a solution plan, committing incrementally, submitting a complete pull request, and maintaining a journal across all four weeks.