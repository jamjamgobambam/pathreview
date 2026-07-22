# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The agent system's `tech_detector.py` tool decides a repository's primary
programming language by counting files per language, but it counts every file
in the repo — including third-party dependencies in `node_modules/` and
compiled output in `build/`. Because those vendored directories are usually
full of JavaScript, a project that is actually written in Python can be
mislabeled as "primarily JavaScript." A successful fix will make the detector
ignore vendored and build-output paths before it counts languages, so the
primary language reflects the code the developer actually wrote. The two
existing tests `test_node_modules_excluded` and `test_build_directory_excluded`
in `tests/unit/test_tech_detector.py` should pass once the filtering is in
place. This affects the agent subsystem (`agent/tools/tech_detector.py`).

**Branch name:** fix/150-tech-detector-vendored-files

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### "Is this right for me?" — scope reasoning

- **Scope is small and well-bounded.** The fix touches a single tool file
  (`agent/tools/tech_detector.py`) plus its test file
  (`tests/unit/test_tech_detector.py`) — no cross-module changes.
- **Clear, reproducible bug.** The issue includes exact reproduction code and
  the expected vs. observed output, so I can confirm the bug and verify the fix
  objectively.
- **Tests already exist.** `test_node_modules_excluded` and
  `test_build_directory_excluded` give me a definition of "done" — the fix is
  correct when they pass, which keeps the change honest.
- **Right tier for a first contribution.** Labeled `tier-1` and
  `good first issue`; the logic is a filtering step, not a design change, so it
  fits a first pass through an unfamiliar codebase.
- **Conclusion:** Good fit — realistic to finish and easy to explain.
