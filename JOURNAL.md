## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The README scorer test uses a sample README that is shorter than the minimum
word count required by the test's own assertion. This causes the test to fail
because of the test data rather than because the scorer is behaving incorrectly.
The issue affects the README scorer unit tests. A successful fix will update the
fixture so it contains enough words while continuing to test the intended scorer
behavior.

**Selection notes — “Is this right for me?” checklist:**
I selected this issue because it is labeled Tier 1 and has a small, clearly
defined scope. The issue appears to involve updating an existing test fixture
rather than changing core application or database logic. I can identify the
relevant unit test, reproduce the failure, make a focused change, and run the
affected tests to confirm the fix. This makes the issue appropriate for my first
contribution to a larger codebase.

**Branch name:** test/156-readme-scorer-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/DelightOti/pathreview/commit/b995ff04b624d17a9d116697a75e0bf796597894]

**Reproduction summary:**  
I activated the project’s virtual environment and ran `python -m pytest tests/unit/test_readme_scorer.py -q`. The test suite produced 1 failed test and 22 passing tests. The failing test expected the README fixture to contain more than 100 words, but the scorer counted only 51 words and categorized it as `minimal`.

**PLAN.md link:** (https://github.com/DelightOti/pathreview/blob/test/156-readme-scorer-fixture/PLAN.md)

**Blockers or open questions:**  
I still need to confirm whether the maintainers prefer expanding the README fixture to more than 500 words or changing the expected category. Based on the test name and existing category tests, expanding the fixture appears to match the intended behavior.

**Blockers:**
Before making my changes, I ran `make check`. It failed with 182 pre-existing lint errors across unrelated files. I will rerun it after my changes to confirm that I did not introduce any new failures.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I reproduced issue #156 and updated the README scorer test fixture so that it
contains enough realistic content to satisfy the intended word-count threshold.
I also updated the related unit test annotations and confirmed that the focused
README scorer tests pass.

**Next steps:**
Request peer or mentor feedback on the pull request, address any relevant
feedback, confirm that my changes introduce no new failures, and finalize the
submission.

**Blockers:**
The repository already had pre-existing lint errors and failing unit tests
unrelated to my issue. I documented the existing failures and compared the
results before and after my changes.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/610

**Branch:** `test/156-readme-scorer-fixture`

**What you built:**
I expanded the README fixture used by the comprehensive README scorer test so
that it contains enough meaningful content to meet the scorer’s word-count
expectation. This fixes the test data without changing the production README
scorer logic.

**Tests added or updated:**
Updated `tests/unit/test_readme_scorer.py`. The focused failing test now passes,
and the complete README scorer test file passes with 23 tests.

**Self-review confirmation:** [x] make check introduces no new failures  [x] make test-unit introduces no new failures

**Draft PR feedback received from:** none yet

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
I did not receive any reviewer feedback. My PR is still open, but there have not been any reviews or comments from maintainers yet.

**How you responded:**
Since I did not receive any feedback, I did not have any changes or responses to make.

---

### Reflection

**What was harder than you expected?**
One thing that was harder than I expected was figuring out what was actually causing the test to fail. At first, I thought there might be something wrong with the README scorer itself, but after looking through the test and the scoring requirements more closely, I realized the problem was actually the test fixture. The README in the test only had 51 words, even though the test expected it to be scored as comprehensive.

Another difficult part was running tests and seeing a lot of errors that had nothing to do with my changes. The repo already had 182 lint errors and 53 failing unit tests before I made my fix, so I had to make sure I was not accidentally blaming my work for problems that were already there.

**What did you learn about working in a large codebase?**
I learned that working in someone else's codebase is very different from working on my own projects. I could not just jump in and change whatever looked wrong. I had to understand how the scorer worked, how the test was supposed to work, and what the original developer was trying to test.

I also learned that sometimes the best fix is actually a small one. For this issue, I did not need to change the README scorer logic at all. I just needed to update the test fixture so it actually matched what the test expected. After I made the change, the focused test passed and all 23 tests in the README scorer test file passed.

**How did AI tools help — and where did they fall short?**
AI helped me a lot with understanding the repo, figuring out what different parts of the code were doing, and helping me troubleshoot errors. It was also useful for Git commands and for helping me understand some of the testing output when I was unsure what it meant.

At the same time, I learned that I could not just trust everything AI suggested. Sometimes I still had to go back into the code myself and check whether the explanation actually made sense. AI also could not automatically tell me which errors were already in the repo and which ones came from my own changes. I still had to test things myself and compare the results.

**What would you do differently if you started over?**
If I started over, I would probably spend more time testing the repo before changing anything. I would run the exact failing test first, then the related test file, and write down what was already failing before I touched the code. That would have made it easier later when I was trying to figure out if I caused any new problems.

I also would have looked at the test fixture and the word-count requirement side by side earlier. Once I realized the fixture only had 51 words, the issue became a lot more obvious.

**What are you most proud of from this module?**
I am most proud that I was able to work through an actual issue in a codebase that I was not familiar with. I was able to reproduce the problem, figure out what was causing it, make a fix, and test it to make sure it worked.

I also feel more comfortable now with using Git, working on a branch, making commits, opening a pull request, and reading through code that I did not write myself. Even though my change was not huge, I feel like I understand the open-source contribution process a lot better now.
