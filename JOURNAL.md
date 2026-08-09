## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117 

**Issue title:** API docs don't include example curl commands

**Tier:** [Y] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is requesting that the API documentation include a working `curl` example so developers can easily test the endpoint from the command line. Currently, the documentation explains the endpoint but does not provide a complete example request, making it harder to verify the API without using another tool. The change affects the project's documentation. A successful fix will add a clear, correct `curl` example that users can copy and run directly.


**Branch name:** fix/117-curl-eg-missing--API-testing

**Setup confirmation:** [Y] App runs locally at localhost:5173

**Cohort ledger:** [Y] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Snehal322/pathreview/commit/974c7ae

**Reproduction summary:**
I reproduced the documentation issue by reviewing docs/api.md and confirming that it lists API endpoints but provides no executable curl examples. This matches Issue #117 because developers currently cannot copy and run example requests directly from the documentation.

**PLAN.md link:**
https://github.com/Snehal322/pathreview/blob/fix/117-curl-eg-missing--API-testing/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
None

## Week 9 - Solution building & PR submission

Check-in 1 (mid-week)

Current progress:
Implemented the API documentation updates for Issue #117. The documentation now covers the available API endpoints, authentication requirements, request examples, successful responses, and error responses. I also ran the existing test suite and identified pre-existing failures unrelated to the API documentation work.

Next steps:
Run make check and make test-unit after the documentation changes, compare the results with the baseline, complete the self-review, and request peer feedback on the draft PR.

Blockers:
The existing unit-test suite contains pre-existing failures in unrelated application components. These are outside the scope of Issue #117.

### Check-in 2 (end of week)

**PR link:** 
https://github.com/ascherj/pathreview/pull/991 

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]
fix/117-curl-eg-missing--API-testing

**What you built:**
Updated the API documentation for Issue #117 to provide a complete reference for the PathReview API, including endpoint descriptions, authentication requirements, request examples, response examples, and documented error responses.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
No unit tests were added because this issue is limited to API documentation and does not modify application logic. The existing test suite was run before and after the changes to verify that the documentation update did not introduce new failures.

Pre-existing failures; no new failures introduced.

**Self-review confirmation:** [Y] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [Y] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No reviewer feedback was received. 

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]
 
--

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
The most difficult part was understanding the difference between a problem with my contribution and problems that already existed in the codebase. My issue, #117, was focused on improving the API documentation, but running make test-unit showed 53 failing tests and make check reported a large number of linting errors. At first, it was tempting to assume that I needed to fix everything before the contribution could be considered complete. After investigating the failures, I found that they were spread across unrelated areas such as resume parsing, skill extraction, safety components, review services, and test files. Learning to distinguish pre-existing failures from problems introduced by my changes was an important part of the contribution process.

Another challenge was working carefully with the repository's existing structure and conventions. Even a seemingly simple documentation change required me to understand which API endpoints actually existed, how authentication worked, and how request and response examples should be represented. I also had to pay attention to the existing file path and naming conventions, such as docs/API.md.


**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
I learned that contributing to an existing codebase requires much more discipline around scope than building a project from scratch. When working on my own projects, I can change the architecture or fix related problems whenever I encounter them. In a shared codebase, that can create unnecessary changes and make a pull request harder to review.

This contribution taught me to start with the issue requirements, inspect the existing implementation and tests, establish a baseline, and then make only the changes necessary for the issue. The pre-existing test and lint failures were especially useful because they showed me why establishing a baseline matters. The goal is not always to make every existing problem disappear; it is to make sure my contribution does not introduce new problems.

I also learned the importance of keeping a clear development history through commits, documentation, testing, and journal entries. These make it easier for another developer to understand what I changed and why.


**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

AI tools were useful for exploring the codebase, understanding existing patterns, interpreting test and lint output, and helping me reason about whether a failure was related to Issue #117. They also helped me think through the API documentation structure and identify the information that should be included in the API reference.

However, AI could not replace reviewing the actual repository and assignment requirements. It initially seemed reasonable to fix the failing tests after seeing the large number of failures, but reviewing the issue scope and the contribution instructions showed that doing so would have expanded the work far beyond Issue #117. AI-generated suggestions also needed to be checked against the actual project structure rather than being accepted automatically.

The biggest lesson was that AI is most useful as a development assistant rather than as the final decision-maker. I still needed to inspect the files, run the commands, compare results before and after my changes, and decide which recommendations were appropriate for the project.


**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]

If I started over, I would establish the baseline earlier and document it immediately. I would run both make check and make test-unit at the beginning, record the existing failures, and then use that baseline throughout the contribution. That would make it easier to recognize immediately that unrelated failures did not need to become part of my issue.

I would also spend more time at the beginning reviewing PLAN.md, docs/CONTRIBUTING.md, the issue requirements, and the existing API documentation before making changes. This would make the implementation more deliberate and reduce uncertainty later in the process.

Finally, I would keep the scope of each commit very clear from the beginning. For a documentation-focused issue like #117, keeping the API documentation changes separate from journal updates and other project work makes the final PR easier to understand and review.


**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I am most proud of learning how to contribute to an existing project without treating every problem I encountered as something I personally needed to fix. Issue #117 looked relatively small because it was primarily an API documentation task, but the surrounding test and lint failures gave me an opportunity to practice real software-engineering judgment. I learned to investigate before changing code, establish a baseline, respect issue scope, use AI critically, and document my work throughout the process.

The most valuable outcome for me was becoming more comfortable working in someone else's codebase and understanding that a good contribution is not necessarily the largest change, it is a focused change that solves the requested problem without making unrelated parts of the project harder to maintain.