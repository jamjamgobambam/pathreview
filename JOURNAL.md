## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The faithfulness checker currently requires at least two meaningful overlapping words between a claim and the retrieved context before it marks the claim as supported. Because of this rule, short factual claims such as “Knows Python” are incorrectly scored as unsupported even when the context clearly mentions Python experience. The issue affects the claim-support logic in `rag/evaluator/faithfulness_checker.py`. A successful fix should allow short claims to be recognized from one meaningful keyword while still keeping stronger matching requirements for longer claims.

**Is this right for me? Selection notes:**

This issue is labeled Tier 1 and has a focused scope in one main component of the codebase. The issue description includes a clear example, identifies the relevant file, and lists related tests, so I can reproduce the problem and verify the fix. The work involves Python, string processing, and unit testing, which are skills I am comfortable using. I also confirmed that the issue was open and not assigned before claiming it.

**Branch name:** `fix/152-short-claim-support`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 – Reproduction & solution planning

**Reproduction commit link:**
[\[link\]](https://github.com/winniehappi1/pathreview/blob/fix/152-short-claim-support/JOURNAL.md)

**Reproduction summary:**

I reproduced Issue #152 by running the faithfulness checker unit tests locally using pytest. The tests showed that short supported claims were incorrectly scored as unsupported, and a None value in a context chunk caused a TypeError.

**PLAN.md link:**
[\[link\]](https://github.com/winniehappi1/pathreview/blob/fix/152-short-claim-support/PLAN.md)

**Walkthrough video:**
Not recorded.

**Blockers or open questions:**
None at this time.

## Week 9
### Check-in 1 (mid-week)

**Current progress:**

I implemented the fix for Issue #152, which addresses the faithfulness checker incorrectly marking short supported claims as unsupported. I updated the matching logic to better handle short factual claims and added handling for `None` values in context chunks to prevent runtime errors. I verified the changes by running the unit tests and confirmed that the previously failing tests now pass.

**Next steps:**

I will run the full project validation commands (`make check` and `make test-unit`), review the implementation for code quality, push the latest changes to my GitHub branch, and open a pull request for review. After that, I will complete the Week 9 Check-in 2 section with the PR link.

**Blockers:**

None at this time.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/651

**Branch:** `fix/152-short-claim-support`

**What you built:**

I updated the faithfulness checker so short factual claims can be recognized as supported when they share a meaningful keyword with the retrieved context. I also improved claim extraction for compound sentences, normalized tokenization to remove punctuation, and made context processing handle missing or `None` text safely.

**Tests added or updated:**

I did not modify the test file. I used the existing tests in `tests/unit/test_faithfulness_checker.py` to validate the implementation, including short-claim support, multiple context chunks, partial support, and `None` context text handling. All 22 tests in that file passed.

**Self-review confirmation:**  
[x] `make check` completed with no new failures introduced  
[x] `make test-unit` completed with no new failures introduced

**Draft PR feedback received from:** none


## Week 10 – Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No – still awaiting review

**Summary of feedback:**

No reviewer feedback was received during the Summer 2026 session. My pull request remained open without maintainer comments.

**How you responded:**

No action was required because no review comments were provided.

---

### Reflection

**What was harder than you expected?**

The hardest part was understanding an unfamiliar production codebase instead of writing code from scratch. Before making any changes, I had to understand how the faithfulness checker fit into the overall retrieval-augmented generation pipeline, identify where to implement the fix, and make sure my changes matched the project's coding style. I also spent a significant amount of time dealing with Git, pull requests, pre-commit hooks, formatting, and type-checking issues before I could successfully submit my work.

**What did you learn about working in a large codebase?**

I learned that contributing to a production repository requires much more than writing working code. It is important to read existing code patterns, follow contribution guidelines, write changes that are consistent with the rest of the project, and ensure tests and formatting tools pass. I also learned to make small, focused changes instead of trying to redesign the entire implementation.

**How did AI tools help — and where did they fall short?**

AI was very helpful for understanding unfamiliar code, explaining Git commands, suggesting implementations, debugging errors, and helping me interpret the issue requirements. However, AI could not determine exactly what the project maintainers expected or guarantee that a solution would satisfy the issue. I still had to read the issue carefully, compare my implementation with the existing codebase, run the tests myself, and make decisions about which suggestions were appropriate.

**What would you do differently if you started over?**

I would spend more time reading the repository before writing code and create my pull request earlier so I would have more time to receive feedback. I would also make smaller commits throughout the process instead of waiting until multiple changes had accumulated, making it easier to track my progress and debug problems.

**What are you most proud of from this module?**

I am most proud that I successfully completed my first contribution to a real open-source project. From selecting an issue and reproducing it to creating a feature branch, implementing a solution, working through Git and pre-commit issues, and submitting a pull request, I gained practical experience with a professional software development workflow that I had never completed before.