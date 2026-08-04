## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**  
The technology detector currently counts files inside directories such as `node_modules/` and `build/` when determining a repository's primary programming language. These directories normally contain third-party dependencies or generated build files rather than code written by the repository owner. As a result, a mainly Python project can incorrectly be classified as JavaScript. A successful fix will exclude these directories from language detection while continuing to count the project's actual source files correctly.

**Selection notes — “Is this issue right for me?” checklist reasoning:**
This issue has a clearly defined problem, reproduction example, and expected result. The work is limited mainly to `agent/tools/tech_detector.py` and the related tests in `tests/unit/test_tech_detector.py`. It is labeled Tier 1 and good first issue, so its scope is appropriate for a first contribution to this codebase. I can verify the solution using the two identified tests for excluding `node_modules/` and `build/`.

**Branch name:** fix/150-ignore-vendored-build-output

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/hedreez09/pathreview/commit/c2dedbe

**Reproduction summary:**
I reproduced issue #150 by running the existing tests for excluding `node_modules/` and `build/` files. Both tests failed because the detector counted JavaScript files in those directories and reported JavaScript as the primary language instead of Python.

**PLAN.md link:**https://github.com/hedreez09/pathreview/blob/fix/150-ignore-vendored-build-output/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
I need to determine whether the fix should normalize both forward-slash and Windows backslash paths while avoiding false matches for similarly named directories.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I reviewed the approved PLAN.md, reproduced the root-level ignored-directory bug, and added a focused failing test for `node_modules/pkg/index.js`. I identified that the existing matching logic required a leading slash, so it failed to recognize ignored directories located at the repository root.

**Next steps:**
Implement the smallest fix by normalizing path separators and matching exact directory components. Then add boundary tests for root-level, nested, absolute, and Windows-style paths while confirming that similarly named directories are not incorrectly skipped.

**Blockers:**
The repository has pre-existing Ruff, mypy, and unit-test failures unrelated to issue #150. I documented their baseline results and kept my changes limited to the issue.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/727

**Branch:** `fix/150-ignore-vendored-build-output`

**What you built:**
I updated the tech detector to exclude files inside ignored directories by matching exact path components. The implementation normalizes Windows and Unix path separators, correctly handles root-level and nested directories, and avoids false positives such as `build_tools` and `node_modules_backup`.

**Tests added or updated:**
Updated `tests/unit/test_tech_detector.py` with one focused reproduction test and five parameterized boundary cases. The complete tech-detector test suite passes with 33 tests, including coverage for root-level, nested, absolute, and Windows-style paths.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

* `make check` still reports 182 pre-existing Ruff errors unrelated to this change.
* `make test-unit` improved from 53 failed and 375 passed to 51 failed and 383 passed. The two issue #150 failures now pass; the remaining failures are pre-existing.

**Draft PR feedback received from:** none
