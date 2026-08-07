# Week 7: Issue Selection

## Selected Issue

**Title:** README scorer test fixture is too short for its own word-count assertion

**Issue:** https://github.com/ascherj/pathreview/issues/156

## Issue Tier

This issue is labeled **Tier 1**. I selected a Tier 1 issue because I am still learning the pathreview codebase and wanted an issue with a clear and manageable scope. It matches my current experience with Python and unit testing while allowing me to become familiar with the project structure.

## Why I Selected This Issue

I chose this issue because it focuses on a single unit test instead of requiring changes throughout the application. The issue is well-defined, making it easier to understand the expected behavior before implementing a fix. Working on this issue will also help me improve my skills in reading existing tests and understanding how they verify application behavior.

## Problem Summary

The issue is about a unit test that uses a sample README which is too short for the expectations in the test. The test is supposed to represent a high-quality README, but the sample content does not contain enough words to satisfy the word-count requirement.

Because of this mismatch, the test can fail even when the README scoring logic is working correctly.

A successful fix would make the sample README and the test expectations agree with each other so that the test accurately verifies the README scorer without producing incorrect failures.


## Is This Right for Me?

- [x] The issue is labeled Tier 1.
- [x] The scope is small and focused on a single unit test.
- [x] I understand what is currently broken after reading the issue and locating the test.
- [x] The issue matches my current Python and testing experience.
- [x] I can complete the work without needing to understand the entire codebase.

I chose this issue because it is small, well defined, and appropriate for my current skill level. It gives me the opportunity to practice reading unit tests and understanding existing code before working on larger or more complex issues.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I completed the reproduction and root-cause analysis from `PLAN.md`. I confirmed that `test_readme_with_all_quality_signals` used a 51-word README fixture while expecting the scorer to classify it as comprehensive. I updated the fixture in `tests/unit/test_readme_scorer.py` so it now exceeds 500 words, preserved the existing quality signals, and changed the word-count assertion to match the comprehensive threshold.

**Next steps:**
I will complete my self-review, confirm the targeted regression test still passes, document the repository’s pre-existing `make check` and `make test-unit` failures, finalize the pull request, and update Check-in 2 with the PR link.

**Blockers:**
The repository already contains unrelated lint, type-checking, and unit-test failures. My targeted test passes, and my changes did not introduce the existing failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/455

**Branch:** `fix/156-readme-scorer-fixture`

**What you built:**
I updated the comprehensive README scorer test fixture so it now exceeds the 500-word threshold while preserving the installation, usage, feature, technology stack, badge, and demo-link quality signals. I also updated the word-count assertion so the test matches the scorer’s documented comprehensive category without changing production scoring logic.

**Tests added or updated:**
Updated `tests/unit/test_readme_scorer.py`, specifically `test_readme_with_all_quality_signals`. The test now verifies that a README with all expected quality signals and more than 500 words is classified as `comprehensive`. The targeted test passes.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

**Pre-existing failures note:**
`make check` and `make test-unit` contain unrelated failures that existed before this change. For this assignment, “passes” means this contribution introduced no new failures. The targeted regression test for Issue #156 passes.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received for PR #455. Reviewer feedback is not provided for the Summer 2026 cohort, so there was no maintainer feedback to address.

**How you responded:**
No response or additional code changes were required because no reviewer feedback was received.

---

### Reflection

**What was harder than you expected?**

The hardest part was figuring out whether the failing test meant the production code was wrong or whether the problem was actually in the test. When I reproduced Issue #156, the test failed because the sample README had only 51 words even though the test expected it to behave like a comprehensive README. I had to look at the scorer logic and the other tests before I understood that the scorer was working correctly and that the test fixture was the actual problem.

I also did not expect the Git and testing workflow to have as many steps as it did. When I tried to commit my change, Ruff, Black, and mypy ran automatically through the pre-commit hooks. Black reformatted the test file, which meant I had to stage the changes again before committing. Mypy also reported existing type annotation errors that were unrelated to Issue #156. This taught me that debugging in a real codebase includes figuring out which failures came from my changes and which ones already existed.

**What did you learn about working in a large codebase?**

I learned that contributing to someone else's codebase is different from building my own small project. I cannot just change something because I think it will fix the immediate problem. I need to understand how the existing code is supposed to work, look at related tests, and make sure my change does not affect unrelated behavior.

For Issue #156, I had to trace the behavior between `tests/unit/test_readme_scorer.py` and `agent/tools/readme_scorer.py`. I learned that a failing test does not automatically mean the production code has a bug. In this case, changing the README scorer would have been the wrong solution because the existing word-count thresholds were working correctly. The safer and more focused solution was to update the test fixture so it actually represented the comprehensive README that the test claimed to be testing.

I also learned why developers try to keep pull requests focused. The repository had other failures that were unrelated to my issue, but trying to fix all of them would have expanded the scope of my work. I kept my implementation focused on Issue #156 instead.

**How did AI tools help — and where did they fall short?**

AI tools helped me understand unfamiliar parts of the codebase and development workflow. They were especially useful when I needed explanations of Git commands, test failures, pre-commit hooks, Ruff, Black, mypy, and the difference between changing production code and changing a test fixture. AI also helped me organize my reproduction steps and `PLAN.md` before implementing the fix.

At the same time, I learned that I cannot automatically accept an AI suggestion without checking the actual repository and command output myself. I still needed to run the tests, read the failure messages, inspect the code, use `git diff`, and confirm exactly what changed. One example was my Week 9 self-review. I checked the boxes saying `make check` and `make test-unit` passed and then explained that they actually contained pre-existing failures. My Week 9 grading feedback pointed out that this could be confusing and that it would have been clearer to state that my contribution introduced no new failures. That showed me that AI can help guide me, but I am still responsible for verifying the result and making sure my final documentation accurately communicates what happened.

**What would you do differently if you started over?**

If I started over, I would establish the testing baseline earlier. Before changing any code, I would run the targeted test, `make check`, and `make test-unit` and record the results. After making my change, I would run the same commands again and compare the results. This would make it easier to prove which failures were already in the repository and whether my change introduced anything new.

I would also be more precise with my documentation and self-review. Instead of checking a box saying that a command passed when the command actually contained unrelated failures, I would clearly state that the command was run, document the pre-existing failures, and state that my contribution introduced no new failures.

I would still choose a focused Tier 1 issue like Issue #156. Because the technical change itself was manageable, I had time to learn the complete contribution process instead of spending all of my time trying to understand a very complicated bug.

**What are you most proud of from this module?**

I am most proud that I completed the full open-source contribution process instead of only making a code change. I started with Issue #156 in a codebase I did not know, reproduced the failure locally, investigated the root cause, wrote a solution plan, implemented a focused fix, tested it, committed and pushed my changes, and submitted PR #455 to the upstream PathReview repository.

I am also proud that I now understand more of the reasoning behind the workflow. Before working through this project, branches, commits, pull requests, testing, and pre-commit checks felt like separate Git and development concepts. Going through the entire process helped me see how they work together when developers collaborate on a shared codebase. I now have a much better understanding of why developers investigate before changing code, keep changes focused, test their work, review their diffs, and clearly document what they changed and why.