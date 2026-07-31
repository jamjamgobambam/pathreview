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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/obwoj1/pathreview/commit/5cec0c3

**Reproduction summary:**
Ran the existing unit suite against the pre-fix `tech_detector.py` and got
`2 failed, 25 passed` — `test_node_modules_excluded` and `test_build_directory_excluded`
both failed, with the tool logging `primary_lang=JavaScript` for a repo whose only
hand-written code is Python (the 6 bundled JS files under `node_modules/` were counted
instead of skipped). This confirms the leading-slash skip patterns never match
top-level vendored/build directories.

**PLAN.md link:** https://github.com/obwoj1/pathreview/blob/fix/150-exclude-vendored-build-files/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
None blocking. One open decision documented in PLAN.md: there's a secondary latent bug
(`primary = sorted(languages)[0]` picks the alphabetically-first language, not the most
common). The two target tests pass with the exclusion fix alone, so I'm keeping scope to
the vendored/build exclusion the issue describes and leaving the tie-break logic alone.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All PLAN.md sub-tasks are done. Replaced the leading-slash substring skip patterns in
`agent/tools/tech_detector.py` with a `SKIP_DIRECTORIES` frozenset and rewrote
`_should_skip_file()` as a `@classmethod` that normalizes separators, splits the path
into segments, and skips a file if any segment is a vendored/build directory. The two
target tests (`test_node_modules_excluded`, `test_build_directory_excluded`) now pass,
and all 27 tech_detector tests are green.

**Next steps:**
Open the PR to `ascherj/pathreview`, fill out the template, and document the
pre-existing codebase failures so reviewers know they're unrelated to this change.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/PENDING

**Branch:** `fix/150-exclude-vendored-build-files`

**What you built:**
Fixed the tech detector so it no longer counts files inside vendored dependency or
build-output directories. The old skip filter used leading-slash substring matching
(`"/node_modules/"`), which silently missed top-level directories; the new filter
matches each path segment against a set of directory names, so `node_modules/lib/x.js`
and nested `packages/app/build/x.js` are both excluded.

**Tests added or updated:**
No new tests needed — the two pre-existing tests `test_node_modules_excluded` and
`test_build_directory_excluded` in `tests/unit/test_tech_detector.py` already defined
the correct behavior and were failing; my change makes them pass (27/27 in that file).

**Self-review confirmation:** [x] make check passes*  [x] make test-unit passes*

\*The codebase has documented **pre-existing** failures unrelated to this issue: on a
clean `main`, `make test-unit` reports 51 failures (review_service, security,
skill_extractor, structural_chunker) and `make check` reports 181 lint errors. My change
introduces **zero** new failures — my file (`agent/tools/tech_detector.py`) passes ruff,
black, and mypy individually, and my module's tests all pass. Per the Week 9 guidance,
"passes" here means my changes make nothing worse.

**Draft PR feedback received from:** none

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
