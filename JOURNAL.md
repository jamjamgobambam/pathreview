## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The tech detector tool (agent/tools/tech_detector.py) analyzes a list of file
paths to determine the primary programming language of a repository. It
currently does not exclude vendored or build-output directories like
node_modules/ or build/ from this analysis. As a result, a repo that is
mostly Python source code but contains several bundled JavaScript files in
node_modules/ or build/ gets misclassified as primarily JavaScript, even
though those files aren't actually part of the project's own source code.
A successful fix will filter out files in these directories before counting
languages, so primary_language correctly reflects the actual source code
rather than vendored dependencies.

**Branch name:** fix/150-tech-detector-exclude-paths

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger




## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/sojsun17/pathreview/commit/d88c906)

**Reproduction summary:**
Ran the exact repro from issue #150 both manually in a Python REPL and via a committed script (`reproduce_issue_150.py`). Confirmed `primary_language` returns `'JavaScript'` instead of the expected `'Python'` when vendored files under `node_modules/` and `build/` are included, and verified the existing `test_node_modules_excluded` and `test_build_directory_excluded` tests fail with the same assertion error. 

**PLAN.md link:** https://github.com/sojsun17/pathreview/blob/fix/150-tech-detector-exclude-paths/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
nothing at the moment


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** Fixed the core bug in _should_skip_file() in agent/tools/tech_detector.py: replaced substring matching ("/build/" in filepath) with path-segment matching (split on /, check for an exact segment match against a SKIP_DIRS set). This correctly excludes root-level vendored/build paths like node_modules/lib/index.js and build/bundle.js, which the old substring check missed because it required a leading / before the directory name. Verified the fix against reproduce_issue_150.py (now returns primary_language = Python as expected) plus three additional manual scenarios: nested skip-dirs still work, filenames that merely contain a skip-dir substring (src/rebuild/utils.py, vendor_utils.py) are correctly NOT skipped, and an all-vendored file list correctly returns Unknown.

Also updated tests/unit/test_tech_detector.py: added 4 new regression tests for the cases above, and filled in assertions on 5 existing tests that called execute() but never actually checked the result (test_vendor_files_excluded, test_dockerfile_detection, test_github_actions_detection, test_makefile_detection, test_framework_detection).

**Next steps:** Run make check and make test-unit locally to confirm no regressions, open a draft PR for peer/mentor feedback, then finalize and submit.

**Blockers:** make check currently reports ~179 pre-existing lint errors across the codebase (unused imports, import ordering, line length, unused variables) in files unrelated to this issue — e.g. rag/retriever/vector_store.py, safety/*.py, and several tests/unit/*.py files. Confirming via a git stash / make check diff that these predate this branch, per the "pre-existing failures" guidance, so they don't block this PR.


---

### Check-in 2 (end of week)

**PR link:** 'https://github.com/ascherj/pathreview/pull/1019'

**Branch:** fix/150-tech-detector-exclude-paths

**What you built:**
Fixed _should_skip_file() in the tech detector to use path-segment matching instead of substring matching, so vendored/build directories at the root of a repo (not just nested ones) are correctly excluded from language detection, resolving the primary_language misclassification described in issue #150
**Tests added or updated:**
tests/unit/test_tech_detector.py — added test_root_level_node_modules_excluded, test_root_level_build_directory_excluded, test_filenames_containing_skip_dir_substrings_not_excluded, and test_all_files_vendored_returns_unknown. Also added missing assertions to 5 existing tests that previously had none.
**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** none