## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Issue selection notes:**

1. Understanding the Issue
   [x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue. See **Problem summary** below.
   [x] I've located the relevant files and confirmed they exist in the codebase. `tests/unit/test_relevance_scorer.py`
   [x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after. See **Problem summary** below.
2. Tier Fit
   [x] If this is my first open source contribution: I'm choosing Tier 1. Furthermore, the issue is tagged as "good first issue".
   [x] If I've contributed to large codebases before: Tier 2 or 3 is fair game. Not applicable here, but acknowledged.
   [x] I'm not choosing a Tier 3 issue to "challenge myself" if I haven't completed a Tier 1 or 2 first — scope surprises in Week 9 don't have a safety net.
3. Codebase Readiness
   [x] I've found and read the specific code the issue references (not just the file — the function or section). `test_query_with_partial_overlap`.
   [x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up. Read this test itself and the surrounding test to ensure my fix doesn't infringe on the other tests.
   [x] I've found the test file for my module and read at least one test end-to-end. My issue itself deals with a test file.
4. Scope and Time
   [x] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue. I chose this issue among my favorite issues since it had the least number of people working on it then.
   [x] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline. It should not take more than 1 hour (not including documentation).
   [x] This issue has no open blockers or dependencies on other unresolved issues. Isolated unit test.

**Problem summary:**

The `test_query_with_partial_overlap` test inside of `test_relevance_scorer.py` tests for partial overlap between the query and chunk, expecting the relevance score to be between `0.3` and `0.9`. However, the test incorrectly sets up a _full_ overlap with the query "Python Django web framework" query and "Django is a Python web framework for rapid development" chunk, resulting in a score of `1.0` and failing the test. Fixing this bug means making the test pass while still adequately testing the underlying functionality. Thus, the test itself must be modified - rather than the implementation - to truly test for partial (not complete) overlap.

**Branch name:** `test/157-relevance-scorer-full-overlap`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
