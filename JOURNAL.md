# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The tech stack detector (`agent/tools/tech_detector.py`) is supposed to skip
vendored and generated files, like `node_modules/` and `build/`, before it
counts languages, but its skip check only matches paths that have a leading
slash in front of the folder name (e.g. `/node_modules/`). File lists come in
as relative paths with no leading slash, so a path like
`node_modules/lib/index.js` slips past the filter and gets counted as a real
source file. On a repo with only a couple of Python files and several
vendored JS files, this pushes the JavaScript count above Python, so
`primary_language` is reported as JavaScript when it should be Python. The
fix is to update the path-matching logic in `_should_skip_file` so it also
catches these directories when they're the first segment of a path. Two
existing unit tests, `test_node_modules_excluded` and
`test_build_directory_excluded`, already assert the correct behavior and are
currently failing — they should pass once the matching logic is corrected.

**Branch name:** fix/150-tech-detector-vendor-build-files

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Scope reasoning ("Is this right for me?"):**
Traced the bug to a single function (`_should_skip_file`) in a single file,
with no database, schema, or cross-module changes involved. The repro steps
in the issue reproduce cleanly against the current code, and two unit tests
already exist that pin down the expected behavior, so the fix is really
about making those tests pass rather than writing test infrastructure from
scratch. Matches the tier-1 "good first issue" label and the 2-3 hour effort
estimate — a good first issue to learn the agent tool module structure
without much risk of scope creep.
