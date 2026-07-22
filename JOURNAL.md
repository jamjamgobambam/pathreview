## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [X] Tier 1

**Problem summary:**
`tech_detector.py` is counting files from folders like `node_modules/` and `build/` when figuring out what the primary language a project uses. These folders usually contain downloaded libraries or generated files (i.e. not the code written by the developer) so they can make the detector pick the wrong language. For example, a Python project with bundled JavaScript files may incorrectly be detected as a JavaScript project. The fix should make the tech detector ignore these directories so that language detection is based only on the project's own source code, allowing the related tests in `tests/unit/test_tech_detector.py` to pass.

**Branch name:** fix/150-ignore-vendored-build-files

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger
