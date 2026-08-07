Week 7 — Issue selection

Issue link: Issue #117 — API docs don't include example curl commands

Issue title: API docs don't include example curl commands

Tier:  Tier 1 

Problem summary:
The PathReview API documentation identifies the available endpoints, but it does not provide command-line examples showing how to call them. This makes it difficult for new contributors to quickly test the API and confirm that their local backend is working correctly. The issue primarily affects docs/API.md rather than the application’s core frontend or backend logic. A successful fix will add clear and accurate curl commands that developers can copy and run against the local API.

“Is this right for me?” checklist reasoning:
I selected this Tier 1 issue because this is my first contribution to the PathReview codebase, and I am still becoming familiar with its architecture and development workflow. The task has a focused scope because the primary file involved is docs/API.md, rather than several interconnected source-code files. I understand the basic technologies involved, including HTTP requests, API endpoints, JSON, and command-line tools, and I can verify the examples by running the application locally. The expected result is also clear and testable: each documented curl command should match a real endpoint and produce the expected API response. Based on its limited scope, defined output, and Tier 1 label, this issue is appropriate for my current comfort level.

Branch name: docs/117-add-curl-examples

Setup confirmation: App runs locally at localhost:5173

Cohort ledger:Issue added to cohort ledger


----------------

# Week 8 — Reproduction & solution planning
(Issue:#157)
**Reproduction commit link:** 
-> https://github.com/Pritigrg/pathreview/commit/90143dc

**Reproduction summary:**
I reproduced the issue by running pytest tests/unit/test_relevance_scorer.py -k partial_overlap -q. The test failed with assert 1.0 < 0.9 because the query and chunk contain all four query keywords, causing the scorer to correctly return a full-overlap score of 1.0 instead of a partial-overlap score.

**PLAN.md link:** 
-> https://github.com/Pritigrg/pathreview/blob/relevance/PLAN.md

<!-- **Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded] -->

**Blockers or open questions:**
I am still confirming whether the corrected test should check an exact expected score, such as pytest.approx(0.5), or only verify that the score is between 0.0 and 1.0.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the fix for issue #157 by updating the partial-overlap test fixture so that only two of the four query terms appear in the retrieved chunk. The reproduction and solution-planning tasks from PLAN.md are complete, and the targeted relevance scorer test now passes.

**Next steps:**
Run the complete unit test suite and project checks, open a draft pull request, request peer or mentor feedback, and address any relevant review comments.

**Blockers:**
None.
### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/436

**Branch:** `test/157-partial-overlap-fixture`

**What you built:**
I corrected the partial-overlap test fixture so that it contains two of the four query terms. The relevance scorer now produces a genuine partial-overlap score of `0.5` instead of the full score of `1.0`.

**Tests added or updated:**
Updated `tests/unit/test_relevance_scorer.py`. The modified test verifies that a chunk containing two of four query terms produces a partial-overlap score of `0.5`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none 

**Pre-existing failures:**
Before my change, `make test-unit` reported 53 failed and 375 passed. After my change, it reported 52 failed and 376 passed. The remaining failures are pre-existing and unrelated to issue #157. `make check` also reports pre-existing repository-wide linting and type-checking issues. My change introduced no new failures.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
I did not receive any reviewer or maintainer feedback.

**How you responded:**
No response was needed because no feedback was received.

---

### Reflection

**What was harder than you expected?**
The hardest part was figuring out whether the problem was in the relevance-scoring code or in the test itself. At first, I assumed the scorer might be wrong because the test was failing. After looking more closely, I noticed that the test called the example “partial overlap,” but the sample text actually contained all four query terms. Because of that, the scorer was correct to return `1.0`.


**What did you learn about working in a large codebase?**
I learned that a failing test does not always mean the production code is broken. Sometimes the test data or expected result is the real problem. It is important to reproduce the issue, understand the logic, and inspect the test carefully before changing the main code.

I also learned that larger repositories may already contain failing tests, lint errors, or type-checking issues. In my case, `make test-unit` showed 53 failed and 375 passed tests before my change. After my fix, it showed 52 failed and 376 passed. This helped confirm that my change fixed the selected issue without creating any new problems.

I also saw the importance of keeping a contribution focused. Since the scorer was already working correctly, I only changed the test fixture instead of making unnecessary changes to the production code.

**How did AI tools help — and where did they fall short?**
AI tools helped me understand the failed test case, logic for the overlap score.

However, I still had to check every suggestion carefully. Some suggestions could have added unnecessary changes, such as fixing unrelated repository errors. I learned that AI can guide the process, but I still need to verify the code, test output, Git diff.

**What would you do differently if you started over?**
I would begin by running only the targeted test and manually comparing the query terms with the sample text. That would have helped me find the real issue faster.

I would also record the original `make check` and `make test-unit` results before changing anything. I would keep the code change as small as possible.

**What are you most proud of from this module?**
I am most proud that I found the real cause of the failure and kept the fix simple. The original fixture contained all four query terms and produced a score of `1.0`. I changed it so that only two of the four terms were present, which produced the intended partial-overlap score of `0.5`.

I am also proud that I verified the result carefully. The full test results changed from 53 failures and 375 passes to 52 failures and 376 passes, showing that my fix worked and did not introduce any new failures.
