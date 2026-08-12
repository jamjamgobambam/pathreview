## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG faithfulness checker combines the `text` values from retrieved context chunks before scoring generated feedback. When a chunk contains the `text` key with a value of `None`, `dict.get("text", "")` returns `None` instead of the empty-string default, and `str.join` raises a `TypeError`. This prevents the checker from returning a score for otherwise valid input. A successful fix will normalize a missing or `None` text value to an empty string so faithfulness evaluation continues without crashing.

**Selection notes — “Is this right for me?” checklist:**
The bug has a narrow scope in `rag/evaluator/faithfulness_checker.py`, includes clear reproduction steps, and already has a focused failing unit test. The expected behavior is explicit, the change does not require an API or database migration, and it can be verified with the targeted test plus the repository's standard checks. These constraints make the issue realistic to complete as a Tier 1 contribution without expanding its scope.

**Branch name:** `fix/153-none-context-chunk-text`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [cf3b1be — fix(rag): handle None context chunk text](https://github.com/yifanliu0108/pathreview/commit/cf3b1be46ca58416f2aacd2dfcd0a731faf6dbb0)

**Reproduction summary:**
I ran `FaithfulnessChecker().check("Knows Python.", [{"text": None}])` against the
upstream implementation and reliably reproduced `TypeError: sequence item 0:
expected str instance, NoneType found` while the context strings were joined. On
this branch, the same input completes without an exception and returns `0.0`.

**PLAN.md link:** [PLAN.md on the working branch](https://github.com/yifanliu0108/pathreview/blob/fix/153-none-context-chunk-text/PLAN.md)

**Walkthrough video (recommended):** Not recorded (optional and not graded).

**Blockers or open questions:**
The issue-specific null-text and missing-key tests pass. Three existing assertions
in the complete faithfulness-checker test module still fail because its current
token-overlap scoring returns `0.0` where those tests expect partial support; they
are unrelated to the `None`-handling crash and are outside issue #153.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented null-safe context concatenation in `FaithfulnessChecker.check()` and
verified the focused `None` and missing-key regression cases. The reproduction,
code mapping, risks, and edge cases in `PLAN.md` are complete.

**Next steps:**
Strengthen the regression coverage for mixed valid, missing, and null context
chunks; run the repository checks; self-review the final diff; and submit the pull
request.

**Blockers:**
The repository has broad pre-existing lint and unit-test failures unrelated to
issue #153. Per the course guidance, I am verifying that the changed files and
focused tests introduce no new failures and documenting the baseline below.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/657

**Branch:** `fix/153-none-context-chunk-text`

**What you built:**
Updated the faithfulness checker so retrieved chunks with missing or `None` text
contribute an empty string instead of crashing `str.join()`. Valid text from other
chunks remains available for scoring.

**Tests added or updated:**
Updated `tests/unit/test_faithfulness_checker.py` to assert the exact score for an
all-null context and added coverage for a mixed list containing valid, missing,
and null chunk text.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Here, “passes” follows the course definition for a codebase with documented
pre-existing failures: the contribution introduces no new failures. On August 3,
2026, `make check` reported 181 existing repository-wide Ruff errors. `make
test-unit` completed with 346 passing tests, 51 existing failures, and 31 errors;
the errors came from chunker tests attempting to download a tokenizer while
network access was unavailable. The focused null/missing-text tests pass, and the
changed Python files pass focused Ruff, Black, and mypy checks.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was provided. Reviewer feedback is not part of the Summer
2026 course process, so my pull request remains open without maintainer comments.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was separating problems caused by my change from failures that
already existed in the repository. The full test suite contained unrelated
scoring failures, lint errors, and tests that tried to download a tokenizer while
the network was unavailable. I had to reproduce issue #153 directly and run
focused tests to prove that my fix handled `None` without introducing a new
failure.

**What did you learn about working in a large codebase?**
I learned that a small code change still requires understanding the surrounding
data flow, existing tests, and project conventions. In my own projects I can
change several components at once, but in someone else's codebase I need to keep
the scope narrow and avoid fixing unrelated problems. Clear notes about the test
baseline also make the contribution easier for a maintainer to evaluate.

**How did AI tools help — and where did they fall short?**
AI tools helped me trace the `TypeError` to `str.join()`, compare possible fixes,
and identify useful edge cases such as missing, null, and mixed chunk text. They
also helped me organize the implementation plan and journal. However, AI could
not decide whether a failure was pre-existing just from the error message. I
still had to inspect the code, reproduce the bug, run the focused tests, and
compare those results with the repository-wide test output.

**What would you do differently if you started over?**
I would run the full checks before changing any code so I had a clear baseline
from the beginning. I would also submit the pull request earlier, leaving more
time to review the final diff and respond if a maintainer commented.

**What are you most proud of from this module?**
I am most proud that I turned a specific crash into a small, tested fix without
expanding the issue's scope. The added tests cover null, missing, and mixed text
values, and the checker now returns a valid score instead of crashing.
