## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The relevance scorer unit test named `test_query_with_partial_overlap` is intended
to verify scoring behavior when only some query terms appear in a document chunk.
However, its current fixture contains all four terms from the query, so the scorer
correctly calculates full keyword coverage and returns a score of 1.0. The test then
incorrectly expects the score to be below 0.9, causing it to fail even though the
scorer is behaving correctly. A successful fix will update the test fixture so that
it contains only some of the query terms and genuinely represents partial overlap.

**Branch name:** test/157-partial-overlap-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes — “Is this right for me?”

This issue appears to have a small and clearly defined scope. It affects an existing
unit-test fixture rather than requiring a change to the relevance-scoring algorithm
or application architecture. The reproduction command identifies the exact test
file and failing assertion, and the expected outcome is clear: revise the fixture so
that only part of the query overlaps with the chunk. This makes the issue appropriate
for my current experience level while still allowing me to practice reading tests,
understanding expected behavior, running targeted checks, and submitting an
open-source pull request.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
https://github.com/douglasem/pathreview/commit/1cab1ac765ea3c1809bbb277cbd196c877017b84

**PLAN.md link:**
https://github.com/douglasem/pathreview/blob/test/157-partial-overlap-fixture/PLAN.md

**Reproduction summary:**
I reproduced the issue by running:

```bash
.venv/bin/pytest tests/unit/test_relevance_scorer.py -q
```

The test test_query_with_partial_overlap failed because it expected a score below 0.9, but the scorer returned 1.0. After reviewing the issue description, I confirmed that the test fixture actually contains all of the query terms, so it represents full overlap rather than partial overlap.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I reproduced Issue #157 and confirmed that `test_query_with_partial_overlap` failed because its fixture contained all four query terms. I inspected `rag/evaluator/relevance_scorer.py` and verified that the scorer calculates keyword overlap as matched query tokens divided by total query tokens. I updated the fixture in `tests/unit/test_relevance_scorer.py` so only two of the four query terms overlap, producing a true partial-overlap score of 0.5. The targeted relevance scorer test file now passes all 19 tests.

**Next steps:**
Run `make check` and `make test-unit`, review the final diff, commit and push the fix, open a draft pull request, request peer or mentor feedback, and complete Check-in 2 before marking the PR ready for review.

**Blockers:**
None.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/802

**Branch:** `test/157-partial-overlap-fixture`

**What you built:**
I corrected the fixture in `test_query_with_partial_overlap` so it now represents genuine partial keyword overlap. The original chunk matched all four query terms and correctly received a score of `1.0`; the updated chunk matches two of four terms and produces the intended score of `0.5` without changing production code.

**Tests added or updated:**
Updated `tests/unit/test_relevance_scorer.py`, specifically
`TestRelevanceScorer.test_query_with_partial_overlap`. The test now covers the case where only some query tokens appear in the retrieved chunk and verifies that the scorer returns a middle-range value rather than full relevance.

**Self-review confirmation:** [x] make check passes (no new failures introduced)  [x] make test-unit passes (no new failures introduced)
Note: The repository contains pre-existing failures that are unrelated to this issue. Both make check and make test-unit have pre-existing failures unrelated to relevance_scorer.py. I confirmed that the changes implemented remove the test failures related to relevance_scorer.py. 

I compared the results against `upstream/main` before submitting my PR.

- `upstream/main`: 375 passed, 53 failed
- This branch: 376 passed, 52 failed

This confirms that my change fixed the targeted relevance scorer test and did not introduce any new failures.

**Draft PR feedback received from:** none (requested peer feedback in Slack but did not receive a response before submission)


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — feedback not required

**Summary of feedback:**

No reviewer feedback had been received by the submission deadline. My pull request remains open and ready for review.

**How you responded:**

N/A

### Reflection

**What was harder than you expected?**

The hardest part was not fixing the issue itself. The hardest part for me was learning how to work within an unfamiliar open-source project. Setting up the development environment took much longer than I expected because I had to install Docker, configure the `.env` file, troubleshoot database connectivity, and understand the project's workflow before I could even reproduce the issue. I also learned that understanding the existing tests was just as important as understanding the production code.

**What did you learn about working in a large codebase?**

I learned that making a small change often requires understanding much more of the surrounding code than I initially expected. For Issue #157, I investigated both `tests/unit/test_relevance_scorer.py` and `rag/evaluator/relevance_scorer.py` before deciding whether production code actually needed to change. That investigation showed the scoring logic was already correct and the real problem was the test fixture itself. Working in an established codebase requires confirming the root cause before making changes.

**How did AI tools help — and where did they fall short?**

AI was extremely helpful for navigating an unfamiliar codebase, understanding the repository structure, explaining how the relevance scorer worked, and helping me troubleshoot environment setup problems. It also helped me understand Git, pull requests, and the contribution workflow. However, AI could not determine whether failing tests or mypy errors were pre-existing project issues or introduced by my changes. I still needed to investigate the repository, compare results against `upstream/main`, and verify everything myself.

**What would you do differently if you started over?**

If I started over, I would spend more time reading the repository documentation before beginning implementation. I would also run the project's full test suite immediately after setting up the environment to establish a baseline of existing failures before making any changes. That would have made it much easier to recognize which issues were unrelated to my contribution.

**What are you most proud of from this module?**

I'm most proud that I resisted changing production code until I fully understood the problem. After investigating the relevance scorer, I realized the implementation was already correct and that the failing test was caused by an incorrect fixture. Fixing the root cause instead of introducing unnecessary code changes helped me better understand how professional open-source contributions should be approached.