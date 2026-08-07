## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Selection reasoning:**
I selected this Tier 1 issue because I am comfortable writing focused unit tests but am still becoming familiar with the project's review API and error-handling flow. The change has a narrow scope in one test file, making it a manageable way to learn how the endpoint handles profiles and ingested content.

**Problem summary:**
The unit tests for the review routes do not cover the case where a valid profile exists but has no associated ingested content. As a result, a regression could cause the `POST /reviews` endpoint to crash instead of returning a controlled error response. The missing coverage belongs in `tests/unit/test_review_routes.py` and should exercise this empty-content condition. A successful change will verify that the endpoint responds with an appropriate error status and message when there is nothing available to review.

**Branch name:** `tests/88-POST-/reviews-endpoint-has-no-test-for-when-the-profile-has-no-ingested-documents-`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Rura-M/pathreview/commit/aa8a1aceeee37329043a67b97f64a86618898087

**Reproduction summary:**
I created a valid profile without a résumé, GitHub username, portfolio URL, or ingested sources, then submitted `POST /reviews` using that profile’s ID. The endpoint incorrectly returns a pending review instead of a controlled 4xx error indicating there is no content to review.

**PLAN.md link:** https://github.com/Rura-M/pathreview/blob/tests/88-POST-/reviews-endpoint-has-no-test-for-when-the-profile-has-no-ingested-documents-/PLAN.md

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented validation for `POST /reviews` so the endpoint confirms that the
requested profile exists, belongs to the authenticated user, and has at least
one associated ingested source before creating a review. I also added
`tests/unit/test_review_routes.py` with a regression test for a valid profile
that has no ingested documents.

**Next steps:**
Review the final diff, commit the implementation and test, push the branch, and
open a pull request. I will also document the repository-wide test failures
that are unrelated to this change.

**Blockers:**
The focused regression test passes, but the full unit suite currently has
pre-existing failures and errors in unrelated modules. Some tests also attempt
to download tokenizer data while network access is unavailable.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/Rura-M/pathreview/pull/1

**Branch:** https://github.com/Rura-M/pathreview/tree/tests/88-POST-/reviews-endpoint-has-no-test-for-when-the-profile-has-no-ingested-documents-

**What you built:**
I updated `create_review_endpoint` to return `404` when the profile is missing
or not owned by the authenticated user and `400` with `"Profile has no
ingested documents"` when the profile has no associated `IngestedSource`
records. The endpoint now stops before creating a review, committing database
changes, or scheduling background processing in the empty-content case.

**Tests added or updated:**
I added `tests/unit/test_review_routes.py`. The test covers an authenticated
request for an existing profile with no ingested documents and verifies the
`400` status and error message, that `create_review` is not called, that no
commit occurs, and that no background task is scheduled.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Focused verification:** [x] regression test passes  [x] Ruff passes  [x] Black passes

`make check` remains blocked by pre-existing type errors in
`core/services/review_service.py`. The full unit suite also contains unrelated
pre-existing failures, so `make test-unit` is not marked as passing.

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review received yet

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Following the flow of data through the codebase was harder than I expected. A single feature could span routes, services, database models, background tasks, and tests, so I sometimes lost track of where a behavior originated. I learned to slow down, trace function calls, and map the dependencies before making changes.

**What did you learn about working in a large codebase?**
I learned that contributing to production code requires more caution than building my own project. In my own projects, I understand most of the decisions because I made them. In an existing codebase, I first have to understand its architecture, conventions, and assumptions. Even a small change can affect other parts of the application, so testing both the expected result and unwanted side effects is important. For example, my test verified not only the error response, but also that no review was created, no database commit occurred, and no background task was scheduled.

**How did AI tools help — and where did they fall short?**
AI tools helped me trace unfamiliar code, visualize how the different layers connected, and explain concepts such as RAG, embeddings, and LLM-based generation. They were also useful for brainstorming tests and interpreting errors. However, AI could not replace reading the code or running the tests. Its suggestions sometimes lacked project-specific context, and it could not always distinguish problems caused by my changes from pre-existing test failures. I still had to verify every suggestion and decide whether it matched the intended behavior.

**What would you do differently if you started over?**
I would also run the full test suite at the beginning to identify pre-existing failures and avoid confusing them with regressions from my work. Finally, I would make smaller changes and test each one immediately.

**What are you most proud of from this module?**
**What was harder than you expected?**  
Following the flow of data through the codebase was harder than I expected. A single feature could span routes, services, database models, background tasks, and tests, so I sometimes lost track of where a behavior originated. I learned to slow down, trace function calls, and map the dependencies before making changes.

**What did you learn about working in a large codebase?**  
I learned that contributing to production code requires more caution than building my own project. In my own projects, I understand most of the decisions because I made them. In an existing codebase, I first have to understand its architecture, conventions, and assumptions. Even a small change can affect other parts of the application, so testing both the expected result and unwanted side effects is important. For example, my test verified not only the error response, but also that no review was created, no database commit occurred, and no background task was scheduled.

**How did AI tools help—and where did they fall short?**  
AI tools helped me trace unfamiliar code, visualize how the different layers connected, and explain concepts such as RAG, embeddings, and LLM-based generation. They were also useful for brainstorming tests and interpreting errors. However, AI could not replace reading the code or running the tests. Its suggestions sometimes lacked project-specific context, and it could not always distinguish problems caused by my changes from pre-existing test failures. I still had to verify every suggestion and decide whether it matched the intended behavior.

**What would you do differently if you started over?**  
I would begin by studying the architecture documentation and drawing a small map of the request flow before changing any code. I would also run the full test suite at the beginning to identify pre-existing failures and avoid confusing them with regressions from my work. Finally, I would make smaller changes and test each one immediately.

**What are you most proud of from this module?**  
I am most proud that I developed a practical understanding of how LLM applications work, including ingestion, chunking, embeddings, retrieval, and generation. I also contributed a focused production fix and regression test that prevent the system from creating a review when a profile has no ingested documents. This showed me that I can navigate an unfamiliar codebase and make a small but meaningful improvement.