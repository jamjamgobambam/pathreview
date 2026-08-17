## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/97

**Issue title:** Review progress indicator doesn't update in real time during long-running reviews

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**

During a long-running review, the user currently sees a fixed loading spinner instead of progress that changes as the review runs. This can make the application appear stuck even when the review is still processing normally. The backend already provides review status information, but the frontend is not currently reflecting those updates in real time. A successful fix would restore meaningful progress feedback on the review page, primarily around `ReviewPage.tsx` and `useReviewStatus.ts`.

**Branch name:** `fix/97-review-progress-indicator`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Issue selection notes

I chose this issue because the problem is clearly defined and has a visible impact on the user experience. The issue identifies `frontend/src/pages/ReviewPage.tsx` and `frontend/src/hooks/useReviewStatus.ts` as clear starting points, and I have read the relevant code to understand how the current polling and loading behavior works.

The expected before-and-after behavior is also concrete. Today, a long-running review only shows a static spinner, which makes it difficult to tell whether processing is still active. After the fix, the review page should reflect changing progress or status information while the existing polling flow continues to run.

I am comfortable taking on this Tier 3 issue because I can trace the React hook, API polling flow, TypeScript types, and the surrounding review-page logic well enough to form a rough implementation plan. I also investigated the existing frontend tests and confirmed that there are currently no tests specifically for `ReviewPage.tsx` or `useReviewStatus.ts`, so I know new coverage will likely need to be added.

The scope appears realistic for Weeks 8–9, and the issue does not list any unresolved blocker or dependency. The main risk is that further investigation may reveal that frontend types, backend progress fields, or additional tests also need changes, so I will verify the API contract before deciding the final implementation scope.

I also checked the issue comments and know that multiple students have already expressed interest in Issue #97. Since CodePath treats claims as non-exclusive, I am comfortable proceeding with the issue.

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** (https://github.com/bhawan-kumar/pathreview/commit/10fd6f7)

**Reproduction summary:**
I reproduced the issue locally by logging into the PathReview app, starting a new portfolio review, and following the review flow to the results page. During processing, the review experience did not show any meaningful progress information, and the status response ultimately returned `progress_pct: 0`, confirming that the current flow does not provide real progress updates to the user.

**PLAN.md link:** https://github.com/bhawan-kumar/pathreview/blob/fix/97-review-progress-indicator/PLAN.md

**Walkthrough video (recommended):** (https://www.loom.com/share/a43217fe76cb4701932628f80e19a839)

**Blockers or open questions:**
The remaining design decisions are how to represent coarse progress milestones and how strictly to type the status response. I’ll resolve those in `PLAN.md` while keeping the existing polling architecture.

## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**  
I completed the core implementation for Issue #97. From the user’s perspective, the main problem was that a long-running review looked stuck because the review page only displayed a static spinner even though processing was still happening in the background. I traced the full flow from the frontend polling hook to the status API and review-processing service and found that the UI had no meaningful progress value to display because `progress_pct` was not persisted or updated during processing.

To fix this, I added a persisted `progress_pct` field to the review model and created a database migration for it. I then updated the review-processing pipeline to write coarse progress milestones as each major stage completes. The review status endpoint now exposes that value through a typed response, and the frontend polling flow consumes the latest progress value and renders it as an accessible progress bar with a visible percentage instead of showing only a spinner.

I also added backend and frontend tests to cover the new behavior. The backend tests verify that new reviews start at `0%`, progress moves forward through the processing stages, successful reviews reach `100%`, and processing failures do not falsely report completion. The frontend tests verify that the progress bar displays the polled percentage correctly and falls back safely to `0%` when no progress value is available.

**Next steps:**  
Complete final self-review, open the pull request, fill out the PR template, add the PR link to this journal, and submit the working branch URL through the course portal.

**Blockers:**  
The repository has pre-existing lint, type-check, and unit-test failures unrelated to Issue #97. I compared the failures against the baseline before my implementation and confirmed that my changes introduced no new failures. All newly added Issue #97 tests pass.


### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/1036)

**Branch:** `fix/97-review-progress-indicator`

**What you built:**  
I implemented end-to-end live progress reporting for long-running reviews. Instead of leaving the user on a static loading state with no indication that work is progressing, the backend now persists progress as the review moves through its major processing stages, the status endpoint returns the latest percentage, and the review page displays that value through an accessible live progress bar. This preserves the existing polling architecture while making the review experience much clearer to the user.

The implementation includes the database, backend service, API contract, frontend polling flow, and UI. I added the `progress_pct` field and migration, initialized new reviews at `0%`, persisted milestones during processing, returned progress through a typed `ReviewStatusResponse`, updated the frontend API and hook types, and replaced the static processing indicator with a percentage-based progress bar.

**Tests added or updated:**  
Updated `tests/unit/test_review_service.py` with tests covering:

- new reviews starting at `0%`
- progress advancing monotonically through processing milestones
- successful reviews reaching `100%`
- failure behavior preserving the last meaningful progress value instead of reporting false completion

Added `frontend/src/pages/__tests__/ReviewPage.test.tsx` with tests covering:

- rendering the live progress bar with the current polled percentage
- correct progress-bar accessibility attributes
- safe fallback to `0%` when `progress_pct` is unavailable

All 3 newly added backend tests and both newly added frontend tests pass.

**Self-review confirmation:**  
- [x] `make check` run - the command still reports documented pre-existing repository lint/type-check failures, but comparison with the baseline confirmed that Issue #97 introduced no new failures.
- [x] `make test-unit` run - the existing backend baseline remains at 53 failures / 378 passes, and all newly added Issue #97 backend tests pass. The new frontend tests also pass.

**Draft PR feedback received from:** none as I am working on the project a bit late

## Week 10 - Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No - No FeedBack

**Summary of feedback:**  
No reviewer feedback was received. As noted for Summer 2026, reviewer feedback is not part of the current PathReview process.

**How you responded:**  
No response or additional changes were required.

---

### Reflection

**What was harder than you expected?**

The hardest part was understanding an unfamiliar codebase before making changes. Issue #97 initially looked like a simple frontend progress-indicator problem, but after tracing the review flow, I realized the behavior depended on how progress was represented and passed through different parts of the application.

This taught me to understand the complete flow first instead of immediately changing the most visible component.

**What did you learn about working in a large codebase?**

I learned that working in an existing production codebase requires much more discipline than building something from scratch. I had to understand existing architecture, conventions, dependencies, and tests before deciding where a change belonged.

I also learned that a good contribution is not only about making the code work. The implementation should fit naturally into the existing system, be testable, maintainable, and easy for another engineer to review.

**How did AI tools help - and where did they fall short?**

I used AI mainly as a tool to help me understand unfamiliar parts of the codebase, trace relationships between files, and explore possible approaches.

I did not rely on AI to make the final engineering decisions. The implementation approach, architecture decisions, production considerations, testing, validation, and final changes were decided and verified by me based on the actual repository.

AI helped speed up my understanding, but the repository code, tests, documentation, and runtime behavior remained my source of truth. I treated AI suggestions as possibilities to investigate rather than decisions to automatically follow.

**What would you do differently if you started over?**

I would map the complete feature flow earlier before thinking about implementation. I would identify where the review starts, how its state changes, how progress reaches the frontend, and which tests cover that behavior.

That would make the investigation more structured and reduce time spent exploring directions that may not fit the existing architecture.

**What are you most proud of from this module?**

I am most proud of improving the way I approach an unfamiliar production codebase.

Instead of treating the task as simply fixing a visible bug, I reproduced the issue, studied the existing implementation, documented my findings, created a solution plan, made the changes carefully, validated them, and prepared the contribution in a way that another engineer could review.

The biggest takeaway for me was learning to understand the system first and then make the smallest appropriate production-quality change.