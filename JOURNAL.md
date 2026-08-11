## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88#top

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is that there is currently no test case for when a profile exists but has no associated ingested documents. In this situation, the review endpoint should handle the missing content gracefully rather than crashing. The test should verify that the endpoint returns an appropriate error response when no ingested documents are available. This mainly affects the review route logic in `api/routes/reviews.py` and its related tests.

Is this right for me?
- I can explain the issue: the review endpoint needs a test for when a profile exists but has no ingested content.
- I found the relevant route in `api/routes/reviews.py`.
- The issue references `tests/unit/test_review_routes.py`, which does not currently exist, so I may need to create it.
- I found `tests/unit/test_review_service.py` and will use it to understand the project’s testing style.
- “Done” means the endpoint returns an appropriate error instead of crashing.
- This is a Tier 1 issue with a small, localized scope, which is a good fit for my first contribution.
- The estimated 2–3 hours is realistic for me.
- I will check the issue comments/ledger for other claims and confirm there are no blockers.

**Branch name:** (test/88-review-no-test-when-no-ingest)

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]
https://github.com/dkn345/pathreview/commit/7c7a7f711980797228581e27062d965b40674808

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
I reproduced the issue by checking whether the referenced test file existed using `test -f tests/unit/test_review_routes.py && echo "FILE EXISTS" || echo "FILE MISSING"`. The command returned `FILE MISSING`, confirming that the route-level test file for this scenario is not present in the current repository.

**PLAN.md link:** [Link Text](PLAN.md)

**Walkthrough video (recommended):** Not available

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I created `tests/unit/test_review_routes.py` and added a unit test for the `POST /reviews` error path when no ingested documents are available. The test verifies that the route preserves the controlled HTTP error and does not schedule background processing.

**Next steps:**
I will commit and push the test, open a draft pull request, request peer or mentor feedback, address any relevant feedback, and finalize the PR.

**Blockers:**
The repository has pre-existing lint and unit-test failures unrelated to my change. My new test passes independently, and Ruff passes for `tests/unit/test_review_routes.py`.

---

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/998)

**Branch:** `test/88-review-no-test-when-no-ingest`

**What you built:**
I added route-level test coverage for the `POST /reviews` error path when no ingested documents are available. The test confirms that the endpoint preserves the controlled `400 Bad Request` response and does not queue the background review-processing task.

**Tests added or updated:**
Created `tests/unit/test_review_routes.py` with `test_profile_no_ingested_docs`. The new test passes independently.

**Self-review confirmation:** [] make check passes  [] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"] 
none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
I found navigating the exact files and understanding the behavior of the function to be a bit difficult since there were many "reviews" under many folders. I had to write a test for a review of profile with no documents and tracing the behavior was slightly difficult due to many versions being there. I was not expecting the function to span multiple folders, so that aspect surprised me.

**What did you learn about working in a large codebase?**
I found contributing to someone else's production code both easier and more difficult than my own project. The aspects I found easy was that there was already a layout to start off with which meant I did not have to plan from scratch. However, the difficult aspect was that there was already so much and I got overwhelmed trying to figure things out. What I learned was to leverage AI in this step especially since it can speed up ones understanding of the files and how they interact. By understanding quicker, the bug fix can also be quicker.

**How did AI tools help — and where did they fall short?**
AI was useful on understanding what to do with unfinished information. For my part, I was confused on the behavior of the review as the text files did not clearly show whether there was an error catching mechanism that I need to write a test for or do the whole logic on my own. In this case, AI helped me with the confusion and I got test cases that could help whether or not the logic was finished. What AI could not help with was the context. I knew the context and what files to model off of along with running and verifying the test was accurate. 

**What would you do differently if you started over?**
I would try to take more time with the understanding of the codebase instead of jumping straight in. Although I was better at being patient and understanding the code, I feel like I still rushed the process. Hence, I would take more time familiarizing, using AI for clarifying questions, and maybe even map out essential parts before going to the bug.

**What are you most proud of from this module?**
I am proud that I contributed to an open source project. This area has been intimidating for me, but I am glad I got out of the comfort zone and navigated through unfamiliar areas. I realized especially with many tools at hand that open source is not as intimidating and is more welcoming than expected.