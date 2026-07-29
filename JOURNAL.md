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