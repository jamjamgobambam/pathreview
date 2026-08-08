## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The technology detector currently counts files inside directories such as `node_modules/` and `build/` when deciding a repository’s primary programming language. These files are usually third-party dependencies or generated build artifacts rather than code written by the repository owner. As a result, a mostly Python project can incorrectly be classified as JavaScript when vendored JavaScript files outnumber the real source files. A successful fix would filter out these paths before counting languages so the detector reflects the repository’s actual source code.

**Issue selection reasoning:**
I chose this issue because it is a Tier 1 bug with a clear reproduction example, a narrow scope, and existing failing tests. The relevant implementation and test files are identified in the issue, so I can trace the problem without needing to understand the entire codebase. The expected behavior is also specific: files inside `node_modules/` and `build/` should not affect primary-language detection. This makes the issue realistic for my current experience while still requiring me to understand and test an existing module.

**Branch name:** fix/150-ignore-vendored-build-files

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger



## Week 8 — Reproduction & solution planning


**Reproduction commit link:** https://github.com/iadamib7/pathreview/commit/2df3497

**Reproduction summary:**
I reproduced Issue #150 by running the existing `test_node_modules_excluded` and `test_build_directory_excluded` tests in `tests/unit/test_tech_detector.py`. Both tests failed because `TechDetector` counted JavaScript files inside `node_modules/` and `build/`, causing it to report JavaScript instead of the expected Python primary language.


**PLAN.md link:** https://github.com/iadamib7/pathreview/blob/fix/150-ignore-vendored-build-files/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
I still need to confirm how file paths are normalized inside `TechDetector` and whether nested or Windows-style paths require additional handling.



## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the fix for Issue #150 in `agent/tools/tech_detector.py`. The detector now normalizes file paths and excludes files located inside vendored or generated directories before performing language detection. The existing `test_node_modules_excluded` and `test_build_directory_excluded` regression tests now pass, and all 27 tests in `tests/unit/test_tech_detector.py` pass.

**Next steps:**
I will open a draft pull request, request peer or mentor feedback, review the repository contribution checklist, and document the repository-wide pre-existing test failures. After addressing any relevant feedback, I will mark the pull request ready for review and complete Check-in 2.

**Blockers:**
The full unit-test suite currently has 51 pre-existing failures in unrelated modules. My focused TechDetector tests pass, and my changes do not touch the failing modules.

**Tests added or updated:**
Updated the TechDetector test coverage by adding regression tests for Windows-style paths, deeply nested vendored/build directories, and filenames that resemble skipped directory names. Verified that all TechDetector unit tests pass.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/551

**Branch:** `fix/150-ignore-vendored-build-files`

**What you built:**
I updated `TechDetector` so files inside vendored dependency and generated build directories do not affect primary-language detection. The implementation normalizes Windows and Unix path separators, checks only directory components, and excludes paths inside directories such as `node_modules`, `build`, `dist`, `vendor`, `.git`, `.venv`, `venv`, and `__pycache__`.

**Tests added or updated:**
I added `tests/unit/test_tech_detector_path_edge_cases.py` with regression tests for Windows-style backslash paths, deeply nested `node_modules` and `build` directories, and valid source files named `node_modules.py` and `build.py`. I also verified that the 27 existing tests in `tests/unit/test_tech_detector.py` and the 3 new edge-case tests all pass.

**Self-review confirmation:** [x] make check passes  [x] focused TechDetector unit tests pass; repository-wide unit suite has documented pre-existing unrelated failures

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback has been provided on my pull request.
As noted in the Summer 2026 course instructions, reviewer feedback is not
provided for this cohort, so I am documenting that no review was received.

**How you responded:**
No response or additional changes were required because I did not receive
reviewer feedback.

---

### Reflection

**What was harder than you expected?**

The hardest part was not the final code change itself, but understanding the
existing repository workflow and making sure my contribution met all of the
project's standards. I had to reproduce Issue #150, trace the behavior to
`agent/tools/tech_detector.py`, understand the existing tests, and work
through formatting, linting, type-checking, and Git requirements. I also
learned that having a working fix is only one part of completing an
open-source contribution; tests, documentation, commits, and the pull
request process are equally important.

**What did you learn about working in a large codebase?**

I learned to make focused changes instead of trying to understand or modify
the entire repository. For Issue #150, I concentrated on
`agent/tools/tech_detector.py` and the related unit tests, reproduced the
failure first, and then changed only the path-filtering behavior responsible
for the bug. I also learned that existing tests and contribution guidelines
are important sources of information because they show the behavior and
standards that maintainers expect. This is different from my own projects,
where I control the architecture and can change several parts of the system
without coordinating with an existing codebase.

**How did AI tools help — and where did they fall short?**

AI tools were useful for helping me interpret test failures, understand the
TechDetector logic, plan the fix, and troubleshoot Git, pytest, formatting,
and type-checking errors. They also helped me think about edge cases such as
Windows-style paths and nested vendored directories. However, I learned that
I could not rely on AI output without verifying it against the repository.
At one point, changes to the test file introduced linting and type-checking
problems, so I had to use the actual pytest, Ruff, Black, mypy, Git, and
repository results to determine what was correct. The biggest lesson was
that AI can accelerate investigation and debugging, but the codebase,
tests, and contribution requirements remain the source of truth.

**What would you do differently if you started over?**

I would read the complete grading rubric and `CONTRIBUTING.md` before making
my first change and maintain a checklist for every required deliverable. I
would also add my own edge-case tests earlier instead of relying initially
on only the existing regression tests. Most importantly, I would verify the
final GitHub branch, `JOURNAL.md`, test commits, PR description, and PR status
against the rubric before submitting. This would have helped me avoid the
documentation and submission problems I encountered during Week 9.

**What are you most proud of from this module?**

I am most proud that I worked through a real bug from reproduction to a
tested implementation rather than stopping once the two original failing
tests passed. My final TechDetector change handles vendored and generated
directories while accounting for both Unix and Windows path separators, and
I added regression coverage for additional path edge cases. More broadly,
I am proud that I became more comfortable navigating an unfamiliar
repository, diagnosing failures, using Git branches and commits, and
preparing a contribution for review.