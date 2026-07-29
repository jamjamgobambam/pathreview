## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [X] Tier 1

**Problem summary:**
`tech_detector.py` is counting files from folders like `node_modules/` and `build/` when figuring out what the primary language a project uses. These folders usually contain downloaded libraries or generated files (i.e. not the code written by the developer) so they can make the detector pick the wrong language. For example, a Python project with bundled JavaScript files may incorrectly be detected as a JavaScript project. The fix should make the tech detector ignore these directories so that language detection is based only on the project's own source code, allowing the related tests in `tests/unit/test_tech_detector.py` to pass.

**Branch name:** fix/150-ignore-vendored-build-files

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** c052e64

**Reproduction summary:**
Ran `.venv/bin/pytest tests/unit/test_tech_detector.py -v -m unit`. 2 of 27 tests fail: `test_node_modules_excluded` and `test_build_directory_excluded`, both expecting `primary_language == "Python"` but getting `"JavaScript"`. Root cause: `_should_skip_file` in `agent/tools/tech_detector.py` checks for substrings like `"/node_modules/"` and `"/build/"` which require a leading slash, but repo-relative paths (e.g. `node_modules/lib/index.js`, `build/bundle.js`) have no leading slash, so the skip patterns never match and vendored/build files aren't filtered out.

**PLAN.md link:** [Click Here](PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]
