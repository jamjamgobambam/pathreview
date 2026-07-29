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

**Cohort ledger:** [x] Issue added to cohort ledger

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

## Week 8 — Reproduction & solution planning

**Reproduction summary:**
Ran the two vendored/build exclusion tests against the current code and both
fail: `primary_language` comes back `"JavaScript"` instead of `"Python"`, and
the tool log reports `languages_count=2` — confirming the vendored
`node_modules/` and build-output `build/` JavaScript files are being counted
instead of skipped. Root cause: the `/node_modules/` and `/build/` patterns in
`_should_skip_file()` are slash-wrapped, so they only match mid-path and miss
root-relative paths (no leading slash); those files survive the filter and are
counted, and `sorted(languages)[0]` then picks `"JavaScript"` alphabetically.

Reproduction command and observed output:

```text
$ .venv/Scripts/python -m pytest tests/unit/test_tech_detector.py \
    -k "node_modules_excluded or build_directory_excluded" -v

>       assert data["primary_language"] == "Python"
E       AssertionError: assert 'JavaScript' == 'Python'
[info] tech_detected  frameworks_count=0 languages_count=2 primary_lang=JavaScript

FAILED tests/unit/test_tech_detector.py::TestTechDetector::test_node_modules_excluded
FAILED tests/unit/test_tech_detector.py::TestTechDetector::test_build_directory_excluded
2 failed, 1 passed, 24 deselected
```
