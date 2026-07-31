## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1 [ ] Tier 2  [ ] Tier 3

**Problem summary:**

Currently, there is a bug in `tech_detector.py` where it fails to exclude `node_modules/` and `build/`. This impacts the evaluation logic: when these directories are included, the high volume of build and configuration files causes `tech_detector.py` to mislabel the repository, rather than ignoring them and labeling it based on the actual source files. The root cause is likely in `tech_detector._should_skip_file`, where the `node_modules/` and `build/` paths are missing from the filter list. Once a successful fix is merged the failing unit test for `tech_detector` should pass and the app should correctly label repos where there is a higher volume of build / configuration files compared to source files.

**Branch name:** fix/150-tech-detector-fails-to-detect-config-files-and-mislabels-repo

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

`tech_detector.py` does not exclude `node_modules/` or `build/` paths. A repo with 2 Python source files and 6 vendored/bundled JS files is reported as primarily JavaScript.

**Is this right for me:** 

**Selection Note:** 

- Part 1: Understanding the Issue

    - [x] I can explain the problem and the expected behavior.
    - [x] I've located the relevant files and confirmed they exist in the codebase.
    - [x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

- Part 2: Tier Fit

    - Is the tier a realistic match for where I am right now?
    - yes, this is my first open source commit so I am choosing tier 1.

- Part 3: Codebase Readiness

    - [x] I've found and read the specific code the issue references
    - [x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
    - [x] I've found the test file for my module and read at least one test end-to-end.

- Part 4: Scope and Time

    - [x] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
    - [x] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
    - [x] This issue has no open blockers or dependencies on other unresolved issues.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Dennis-1am/pathreview/commit/9fbd1d6f7839231abf799de89b46d1f3c0a2108b

**Reproduction summary:**
I reproduced the issue by running the test case for it and observing that the test fails because it mislabeled the test repository. The specific test that I observe the failure in is in this:

```
def test_node_modules_excluded(self, detector):
    """Test node_modules/ directory is excluded from counts."""
    files = [
        "src/main.py",
        "node_modules/package1/index.js",
        "node_modules/package2/lib.js",
        "utils.py",
    ]

    result = detector.execute({"files": files})

    data = result.data
    assert data["primary_language"] == "Python"
    # node_modules shouldn't dominate
```

**PLAN.md link:** http://github.com/Dennis-1am/pathreview/blob/tree/fix/150-tech-detector-fails-to-detect-config-files-and-mislabels-repo/PLAN.md

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have implemented the fix for this issue using claude to help identify and put up a initial fix then iterate on it.

**Next steps:**
Document the fix and open the PR up for this and confirm that existing test still pass and failing test now passes.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/417

**Branch:** tree/fix/150-tech-detector-fails-to-detect-config-files-and-mislabels-repo

**What you built:**
The fix adds the missing node_modules/ & build/ from the should skip filter.

**Tests added or updated:**
No test needed to be updated. Test referenced in `tech_detector_test.py`. Previously, failing test now pass as well.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** slack handle: ssangela cui