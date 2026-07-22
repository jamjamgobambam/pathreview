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
