# Module 3 Journal — PathReview

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `TechDetector` tool (`agent/tools/tech_detector.py`) guesses a repository's primary language by
counting source files per language. It's supposed to ignore vendored dependencies and build output, and
it has a `_should_skip_file()` filter for that — but the skip patterns are written with leading slashes
(`"/node_modules/"`, `"/build/"`, `"/dist/"`, etc.), so they only match those directories when nested,
not when they sit at the top of a path (`node_modules/lib/index.js`). As a result, top-level vendored and
build files aren't excluded and inflate the language counts, so a repo with 2 Python files and 6 bundled
JS files gets reported as "JavaScript." A successful fix makes the exclusion match these directories
whether they appear at the start of a path or nested inside it, so the two failing tests
(`test_node_modules_excluded`, `test_build_directory_excluded`) pass and the primary language reflects
the code the user actually wrote.

**Branch name:** fix/150-exclude-vendored-build-files

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" — scope notes
- **Single file, tightly scoped:** the fix lives entirely in `agent/tools/tech_detector.py` (the
  `_should_skip_file` path-matching logic). No cross-module changes, no schema/API changes.
- **"Done" is objective:** two existing unit tests (`test_node_modules_excluded`,
  `test_build_directory_excluded` in `tests/unit/test_tech_detector.py`) already define the expected
  behavior — success = make them pass without breaking the others.
- **No new dependencies** and no external services needed to reproduce (pure Python function with a file
  list input).
- **In my skill range:** it's Python string/path matching — I can reason about it fully and explain the
  root cause, which fits a Tier 1 first contribution.
- **Watch-out I noted:** there's a secondary quirk (`primary = sorted(languages)[0]` picks the
  alphabetically-first language, not the most common). The reproduction is fixed by the exclusion change
  alone; I'll keep the scope to the vendored/build exclusion the issue describes and only touch the
  primary-language logic if the tests require it.
