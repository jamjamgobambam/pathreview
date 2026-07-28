## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150
**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `TechDetector` class in `agent/tools/tech_detector.py` scans all files passed to it when
determining a repo's primary language, without excluding vendored or build-output directories
like `node_modules/` and `build/`. Because these directories typically contain far more files
than actual source code, a repo with mostly Python source can still get misclassified as
JavaScript — for example, 2 real Python files alongside 6 bundled JS files in `node_modules/`
and `build/` currently reports `'JavaScript'` as the primary language instead of `'Python'`. A
successful fix would add path-based filtering so common vendored/build directories are excluded
before language counts are tallied, which should make the two currently-failing tests
(`test_node_modules_excluded`, `test_build_directory_excluded`) pass.

**Scope reasoning:**
This is a Tier 1 issue and a good fit as my first contribution — the fix is isolated to
`agent/tools/tech_detector.py`, doesn't require understanding how the detector interacts with
the rest of the agent system, and comes with two existing failing tests
(`test_node_modules_excluded`, `test_build_directory_excluded`) that define exactly what
"done" looks like. I read both tests and the relevant function before claiming this issue.
I checked the issue comments and cohort ledger and I'm comfortable with the number of
students also on this issue. I don't see any blockers referenced. I estimate this will take
3–4 hours given the clear repro steps, which fits comfortably within the Tier 1 time budget
for Weeks 8–9.

**Branch name:** fix/150-vendored-build-output-detection

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [ADD LINK AFTER YOU COMMIT — run `git log -1 --format="%H"` after committing, then use https://github.com/faisalkhansk3283/pathreview/commit/<hash>]

**Reproduction summary:**
Ran the repro snippet from issue #150 against `TechDetector.execute()` with 2 Python files and
6 vendored/build JS files (`node_modules/`, `build/`) — it returned `primary_language:
"JavaScript"` instead of the expected `"Python"`. Traced this to `_should_skip_file()` in
`agent/tools/tech_detector.py:143`, whose skip patterns (e.g. `"/node_modules/"`) require a
leading `/` that repo-root-relative paths don't have, so vendor/build files are never filtered.
Confirmed via `pytest tests/unit/test_tech_detector.py -v` that `test_node_modules_excluded`
and `test_build_directory_excluded` currently fail for this exact reason.

**PLAN.md link:** https://github.com/faisalkhansk3283/pathreview/blob/fix/150-vendored-build-output-detection/PLAN.md

**Walkthrough video (recommended):** https://imgur.com/a/zR11cvH

**Blockers or open questions:**
None currently — root cause is isolated and the fix path is clear (segment-based path
matching instead of slash-wrapped substring matching).
