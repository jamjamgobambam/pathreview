# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview’s technology detector is supposed to ignore dependency and generated-output directories when determining a repository’s programming languages. However, its current skip patterns contain leading slashes, so root-level paths such as `node_modules/package/index.js` and `build/bundle.js` are not excluded. As a result, vendored or generated JavaScript files can affect language detection and cause the repository’s primary language to be reported incorrectly. A successful fix will make the filtering logic work for both root-level and nested directories while passing the existing unit tests.

**Selection notes — “Is this issue right for me?” checklist:**

- The expected behavior and current failure are clearly explained.
- The issue includes a reproducible example and identifies relevant failing tests.
- The likely scope is limited to `agent/tools/tech_detector.py` and `tests/unit/test_tech_detector.py`.
- The issue does not require a database migration, external API integration, or major frontend changes.
- I have experience with Python, backend development, file-processing logic, and unit testing.
- I understand the likely cause: root-level paths do not contain the leading slash used by the existing skip patterns.
- I will verify root-level paths, nested paths, and path separators without changing unrelated detection behavior.
- This Tier 1 issue has a realistic scope for my first contribution to this repository.

**Branch name:** `fix/150-ignore-vendored-build-files`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tungnguyenasu/pathreview/commit/41585836d39f3b4ee72b42d29cfb09bf8bff9d6d

**Reproduction summary:**
I reproduced Issue #150 by running the existing `test_node_modules_excluded`
and `test_build_directory_excluded` unit tests. Both tests failed because
root-level `node_modules/` and `build/` paths were not filtered, allowing
JavaScript files in those directories to make JavaScript the reported primary
language instead of Python.

**PLAN.md link:** https://github.com/tungnguyenasu/pathreview/blob/fix/150-ignore-vendored-build-files/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
I need to verify whether path component comparisons should be case-sensitive.
I will also confirm that normalizing Windows backslashes does not change
existing behavior for repository paths that already use forward slashes.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I reproduced Issue #150, traced the problem to the leading-slash substring
patterns in `TechDetector._should_skip_file()`, and completed the solution
plan. I also identified the existing tests that need stronger assertions and
the edge cases that require regression coverage.

**Next steps:**
I will normalize path separators, compare exact directory components, add
regression tests, run the targeted and complete test suites, and open a draft
pull request for feedback.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [paste final non-draft PR link]

**Branch:** `fix/150-ignore-vendored-build-files`

**What you built:**
I updated `TechDetector` to normalize repository paths and ignore exact
dependency, vendor, cache, virtual-environment, and generated-output directory
components. The fix works for root-level, nested, and Windows-style paths
without excluding similarly named legitimate directories.

**Tests added or updated:**
I updated `tests/unit/test_tech_detector.py` to strengthen the existing
`node_modules`, `vendor`, and `build` tests. I also added regression coverage
for nested ignored directories, Windows separators, ignored configuration
files, similarly named valid directories, and inputs where every file is
excluded. The full `tests/unit/test_tech_detector.py` file passes (32 tests).

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

*Note:* Both boxes are left unchecked because the repository has pre-existing,
unrelated failures on `main`: `make test-unit` reports 51 failing tests in
other modules (unchanged by this branch), and `make check` fails on pre-existing
`ruff`/`black`/`mypy` findings in files this change does not touch. The tests
specific to Issue #150 all pass, and `mypy` reports no issues on
`agent/tools/tech_detector.py`.

**Draft PR feedback received from:** none