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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md: rewrote `_should_skip_file` in `agent/tools/tech_detector.py` to split each filepath on `/` and check directory segments (`parts[:-1]`) against a skip-dir set, instead of the old leading-slash substring check. Both target tests (`test_node_modules_excluded`, `test_build_directory_excluded`) now pass. Only sub-task from PLAN.md, so implementation is done.

**Next steps:**
Run full unit suite to confirm no regressions, self-review with `make check`/`make test-unit`, write PR description, push branch and open PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [not yet opened — pending push]

**Branch:** `fix/150-ignore-vendored-build-files`

**What you built:**
Fixed `_should_skip_file` in `agent/tools/tech_detector.py` so it matches skip directories (`node_modules`, `vendor`, `dist`, `build`, `.git`, `__pycache__`, `.venv`, `venv`) by path segment rather than by leading-slash substring, so vendored/build files are correctly excluded from language detection at any depth, including root-level paths.

**Tests added or updated:**
None added or modified. `tests/unit/test_tech_detector.py::test_node_modules_excluded` and `::test_build_directory_excluded` already encoded the expected behavior; the implementation fix was sufficient to make them pass.

**Self-review confirmation:** [X] make test-unit passes (`.venv/bin/pytest tests/unit/test_tech_detector.py -m unit`: 27/27 pass; full `tests/unit` suite: 51 pre-existing unrelated failures, down from 53 before this fix, confirmed on main)  [ ] make check passes (182 pre-existing lint errors repo-wide, unrelated to this change; `agent/tools/tech_detector.py` itself has one pre-existing import-sort warning, not introduced by this fix)

**Draft PR feedback received from:** none