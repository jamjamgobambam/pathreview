# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** ☑ Tier 1  ☐ Tier 2  ☐ Tier 3

**Problem summary:**

The README scorer test expected the README fixture to be categorized as "comprehensive," but the fixture itself did not contain enough words to meet the scorer's threshold. As a result, the test failed even though the scorer's implementation was working correctly. The fix was to update the test fixture so that it satisfied the expected word count while preserving the existing README quality signals, allowing the test to accurately validate the scorer's behavior.

**Branch name:**

`fix/readme-scorer-fixture-156`

**Setup confirmation:**

☑ App runs locally at localhost:5173

**Cohort ledger:**

☐ Issue added to cohort ledger *(Update to ☑ after you add your entry.)*

---

### Selection notes ("Is this right for me?" checklist)

I selected this issue because it is a Tier 1 issue and focuses on understanding an existing test rather than implementing a new feature. I was able to reproduce the failure locally, identify the root cause by reading the test and the README scoring logic, and make a targeted change without modifying production code. The scope was well-defined and appropriate for my first open-source contribution to this project.

### Reproduction

Running:

python -m pytest tests/unit/test_readme_scorer.py -q

initially produced:

AssertionError:
expected "comprehensive"
received "adequate"

The README fixture contained only 251 words, while the scorer classifies
README files with more than 500 words as comprehensive.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**

(To be added after committing.)

**Reproduction summary:**

I reproduced the issue by running the README scorer unit tests. The test
expected the README fixture to be categorized as "comprehensive," but it only
contained enough words to be classified as "adequate," causing the assertion
to fail.

**PLAN.md link:**
https://github.com/wen7726/pathreview/blob/fix/readme-scorer-fixture-156/PLAN.md

**Walkthrough video (recommended):**

Not recorded.

**Blockers or open questions:**

None at this time.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I verified the README scorer thresholds and updated the README fixture
to satisfy the comprehensive word-count category.
The updated fixture now aligns with the production scoring logic.

**Next steps:**

Run the test suite again, review the pull request,
and prepare the final submission.

**Blockers:**

None.

---

### Check-in 2 (end of week)

**PR link:**

https://github.com/ascherj/pathreview/pull/276

**Branch:**

fix/readme-scorer-fixture-156

**What you built:**

Updated the README test fixture so that it exceeds the
"comprehensive" word-count threshold while preserving the existing
quality signals. The production implementation was unchanged.

**Tests added or updated:**

Updated:

tests/unit/test_readme_scorer.py

The existing unit test now validates the intended behavior.

**Self-review confirmation:**

[x] make check passes

[x] make test-unit passes

**Draft PR feedback received from:**

None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes

**Summary of feedback:**
A reviewer confirmed that the updated README test fixture became comprehensive by expanding the test content and repeating it to ensure it consistently exceeded the comprehensive word-count threshold while preserving the existing quality signals.

**How you responded:**
I thanked the reviewer for taking the time to review the PR and confirmed that expanding the fixture while preserving the original quality signals was the intended approach.

---

### Reflection

**What was harder than you expected?**

Understanding an unfamiliar codebase was harder than I expected. Even though Issue #156 was relatively small, I still needed to understand how the README scorer worked, how the existing tests were structured, and why the fixture no longer satisfied the expected category. I also spent a significant amount of time debugging Git, pre-commit hooks, Ruff, and mypy before I could successfully submit my changes.

**What did you learn about working in a large codebase?**

I learned that contributing to an existing project is very different from building my own projects. Instead of designing everything myself, I had to understand existing architecture, coding conventions, and testing patterns before making any changes. Reading existing tests became just as important as reading the implementation itself.

**How did AI tools help — and where did they fall short?**

AI tools helped me understand unfamiliar code, explain existing tests, debug Git issues, and navigate the repository much faster. They were especially useful for understanding project structure and interpreting error messages. However, AI could not determine the correct solution without context. I still needed to verify the implementation, understand the project's conventions, run the tests locally, and confirm that the changes actually solved the issue.

**What would you do differently if you started over?**

If I started over, I would spend more time exploring the codebase before making changes. I would also open my pull request earlier so I could receive feedback sooner and leave more time for revisions before the deadline.

**What are you most proud of from this module?**

I am most proud of successfully contributing to a real open-source project for the first time. Beyond fixing the issue itself, I learned the complete contribution workflow, including reproducing an issue, planning a solution, updating tests, creating a pull request, responding to review feedback, and documenting my work throughout the process.