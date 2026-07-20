# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `TechDetector` agent tool guesses a repo's primary language from its file
list, and it already has skip logic in `_should_skip_file`
(`agent/tools/tech_detector.py`) meant to exclude vendored/build directories
like `node_modules/` and `build/`. The bug is that the skip patterns are
anchored with a leading slash (e.g. `"/node_modules/"`, `"/build/"`), so a
path only gets filtered when that directory is nested under something else —
a top-level path like `node_modules/lib/index.js` or `build/bundle.js` has no
leading `/` before the directory name, so it slips past the filter uncounted.
I confirmed this by reading the code and running the existing suite: the two
tests the issue points to, `test_node_modules_excluded` and
`test_build_directory_excluded` in `tests/unit/test_tech_detector.py`, both
fail against current `main`. A repo with 2 Python files and several
top-level `node_modules`/`build` JS files gets reported as primarily
JavaScript instead of Python. A successful fix matches these directory names
regardless of position in the path (e.g. by checking path segments instead of
a substring that assumes a leading slash), so both currently-failing tests
pass without breaking the ones that already pass (e.g. nested vendor paths
like `src/vendor/lib.js`).

**Branch name:** fix/150-tech-detector-vendored-files

**Setup confirmation:** [x] App runs locally at localhost:5173 (verified:
`make setup` + `make run`, frontend loads at localhost:5173, backend
`/auth/login` issues a working JWT for the seeded `user1@example.com`
account, and `pytest tests/unit` runs — 375 passed / 53 failed, with the
failures matching known-open issues elsewhere in the codebase, not setup
problems)

**Selection notes (scope check):**
- *Understand the code before committing?* Yes — read `tech_detector.py`
  end-to-end (165 lines, one class, no external dependencies) and the
  matching test file. The bug is a one-line class of fix in a single
  `@staticmethod`, not a design change.
- *Is the repro reliable?* Yes — reran the two tests named in the issue
  myself and both fail exactly as described, so the issue is accurately
  scoped and not stale.
- *Blast radius?* Small and contained — `_should_skip_file` is only called
  from `_detect_tech` in the same file; no other module imports it directly
  (checked with a repo-wide search), so a fix here shouldn't ripple outward.
- *Right tier for a first contribution?* Yes — Tier 1 / "good first issue",
  isolated to one file, existing tests define done, no new dependencies or
  migrations needed.
- *Is it still available?* The issue has many "I'll work on this" comments
  from other students (this is a shared tracker across the cohort), but
  that's expected for a popular Tier 1 issue — I commented my own claim on
  2026-07-17 and am tracking it in the cohort ledger per the process below.

**Cohort ledger:** [ ] Issue added to cohort ledger — the ledger lives in the
course portal (a per-section spreadsheet), not in this repo, so it isn't
reachable from here. Still needs to be filled in by hand: name, GitHub
username, issue #150, on the correct section tab.
