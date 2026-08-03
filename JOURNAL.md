## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/miaaoyama/pathreview/commit/c403386

**Reproduction summary:**
I reproduced Issue #152 by running the faithfulness-checker unit tests locally. Several tests involving short or partially supported claims returned a score of `0.0` with zero supported claims, confirming that short claims cannot satisfy the current token-overlap requirement.

**PLAN.md link:** https://github.com/miaaoyama/pathreview/blob/fix/faithfulness-short-claims/PLAN.md

**Walkthrough video (recommended):** https://youtu.be/U4XPfrgAzbU

**Blockers or open questions:**
I still need to confirm the safest adaptive threshold for short claims. The fix must support single-meaningful-token claims without allowing longer claims to pass based on one incidental overlapping word.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for Issue #152 by updating the faithfulness checker to correctly support short claims while preserving stricter matching for longer claims. Updated the related unit tests and confirmed the targeted test suite passes.

**Next steps:**
Run final validation, open a pull request, request peer feedback, and finalize documentation.

**Blockers:**
The repository contains unrelated pre-existing test and lint failures outside the scope of this issue.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/569

**Branch:** `fix/faithfulness-short-claims`

**What you built:**
Updated the faithfulness checker to correctly evaluate short factual claims by using an adaptive overlap threshold. Added regression tests to verify supported and unsupported short claims and improved handling of `None` context values.

**Tests added or updated:**
Updated `tests/unit/test_faithfulness_checker.py` to cover short claims, partial support, multiple supported claims, and edge cases.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** @sh4wnbk on github

**Branch:** `fix/faithfulness-short-claims`

**What was built:**  
I updated the faithfulness checker so short claims can be recognized as supported when their meaningful content appears in the retrieved context. The fix uses a lower overlap threshold for short claims while preserving a stronger threshold for longer claims, and it also handles `None` context text safely.

**Tests added or updated:**  
I updated `tests/unit/test_faithfulness_checker.py` to cover supported and unsupported short claims, partial support, multiple context chunks, varying claim support, and `None` context text. All 23 targeted faithfulness-checker tests pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** sh4wnbk on github

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [X] Yes  [ ] No — from sh4wnbk on github

**Summary of feedback:**
A peer reviewer confirmed that the adaptive overlap threshold correctly addressed the issue and that the updated tests provided good regression coverage. They asked whether relaxing the threshold for two-token claims was an intentional design decision and suggested that the documentation and reproduction files might be better separated from the implementation in a production PR. They also pointed out two journal items that still needed to be completed for the assignment.

**How you responded:**
I clarified that the adaptive threshold for one- and two-token claims was an intentional design decision to better support concise factual resume claims while maintaining a stricter threshold for longer claims. I updated my JOURNAL.md to replace the placeholder reproduction commit link and added the required Week 9 check-in structure before submission.

---

### Reflection

**What was harder than you expected?**

The hardest part was understanding a large codebase that I had never seen before. Finding the files related to my issue and tracing how the faithfulness checker worked took much longer than I expected. I also had to learn how the existing tests were structured so that I could add new tests that matched the project's conventions. Another challenge was distinguishing between failures related to my issue and the repository's pre-existing failures. It was important to understand which problems I was responsible for fixing and which ones were outside the scope of my contribution.

**What did you learn about working in a large codebase?**

Working in a large codebase is very different from working on my own projects. Instead of writing code from scratch, most of the work involved understanding existing code, following the project's style and testing patterns, and making the smallest possible change to solve a specific issue. I also learned that reading existing tests is one of the fastest ways to understand how a component is expected to behave.

**How did AI tools help — and where did they fall short?**

AI was very helpful for navigating the unfamiliar codebase, explaining existing functions, suggesting debugging strategies, and helping me understand regular expressions and Git workflows. However, AI could not replace actually reading the code or interpreting the test results. I still had to verify every suggestion against the repository, adjust the implementation to match the project's design, and determine which failures were related to my issue versus unrelated pre-existing problems.

**What would you do differently if you started over?**

If I started over, I would spend more time reading the project structure and existing unit tests before making any code changes. I would also create a small reproduction case earlier in the process because reproducing the issue helped me understand the bug much more quickly. Finally, I would open my draft PR earlier so I could request feedback sooner.

**What are you most proud of from this module?**

I'm most proud that I was able to contribute a real fix to an unfamiliar open source project from start to finish. I reproduced the issue, developed a solution, updated the tests, opened a pull request, and followed the same workflow used in professional software development. This experience gave me much more confidence that I can contribute to larger engineering projects.
