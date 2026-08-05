PathReview Contribution Journal

Week 7 — Issue selection

Issue link: https://github.com/ascherj/pathreview/issues/152

Issue title: Faithfulness checker can never mark short claims as supported

Tier: [x] Tier 1  [ ] Tier 2  [ ] Tier 3

Problem summary:The faithfulness checker currently prevents short claims from being marked as supported, even when the retrieved evidence clearly supports them. This causes valid short claims to receive a faithfulness score of 0.0. The issue appears to involve both claim extraction and the token-overlap logic used to decide whether a claim is supported. A successful fix will allow short factual claims to receive credit without making longer or unrelated claims too easy to mark as supported.

Branch name: fix/152-short-claims-faithfulness

Setup confirmation: [x] App runs locally at localhost:5173

Cohort ledger: [x] Issue added to cohort ledger

Issue selection reasoning

I chose this issue because it is a Tier 1 issue with a clearly defined problem and expected behavior. The issue appears to be limited to the faithfulness checker, which makes the scope manageable for a first contribution to a large codebase. I was able to locate the relevant implementation and unit tests, and the bug can be reproduced without changing unrelated parts of the application. The main risk is lowering the support threshold too much and creating false positives, so the fix should treat short and long claims differently.

Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/CV17-09/pathreview-issue-152/commit/7821ab77f6e69f5abe98dbe7667fc7cd455e5fef

Reproduction summary:I reproduced the issue by checking the claims “Knows Python. Knows SQL.” against context chunks containing “python expert” and “sql expert.” The checker returned a faithfulness score of 0.0 even though both short claims had matching evidence. I also ran the faithfulness checker unit tests and confirmed that the partial-support, multiple-context, and varying-support tests fail with scores of 0.0.

PLAN.md link: https://github.com/CV17-09/pathreview-issue-152/blob/fix/152-short-claims-faithfulness/PLAN.md

Walkthrough video (recommended): Not recorded.

Blockers or open questions:I need to determine the safest threshold for short claims so that one meaningful matching term can count as support without creating false positives for longer or vague claims.

Reproduction evidence

Command:

pytest tests/unit/test_faithfulness_checker.py -v

Result:

22 tests collected

18 passed

4 failed

Failures related to Issue #152:

test_partial_support_returns_middle_score

test_multiple_context_chunks

test_multiple_claims_varying_support

Additional unrelated failure observed:

test_none_context_chunk_text

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the fix for Issue #152 by updating the faithfulness checker to correctly support short claims with valid evidence. I also improved claim extraction and context matching and verified the behavior using the related unit tests.

**Next steps:**
Run the project checks, create a pull request, update my documentation, and submit my branch for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/CV17-09/pathreview-issue-152/pull/1

**Branch:** `fix/152-short-claims-faithfulness`

**What you built:**
I updated the faithfulness checker so that short claims with supporting evidence are correctly recognized. The implementation improves claim extraction, keyword matching, and safely handles `None` context values while preserving the existing scoring behavior.

**Tests added or updated:**
I verified the implementation using `tests/unit/test_faithfulness_checker.py`. All **22** unit tests for the faithfulness checker passed successfully.

**Self-review confirmation:**
- [ ] make check passes
- [ ] make test-unit passes *(repository contains pre-existing unrelated failures)*
- [x] `pytest tests/unit/test_faithfulness_checker.py -v` passes (22/22)

**Draft PR feedback received from:** None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received during this module, so I did not have any comments to address.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Setting up the development environment and understanding an unfamiliar codebase took longer than I expected. It also took time to trace the bug and understand how the faithfulness checker worked before making any changes.

**What did you learn about working in a large codebase?**
I learned that contributing to an existing project requires understanding the current design and following the project's coding standards instead of simply writing code from scratch. Running tests and making sure changes do not affect other parts of the project is also very important.

**How did AI tools help — and where did they fall short?**
AI helped me understand the codebase, explain the issue, and debug failing tests more quickly. However, I still had to read the code myself, verify the suggestions, and test the implementation because AI could not automatically determine the correct solution for every situation.

**What would you do differently if you started over?**
I would spend more time exploring the project structure before choosing an issue and start testing earlier in the process. That would make it easier to understand how the different components work together.

**What are you most proud of from this module?**
I am most proud that I successfully reproduced the issue, implemented a working fix, and got all 22 faithfulness checker unit tests to pass while following the complete GitHub contribution workflow.