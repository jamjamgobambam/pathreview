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

**Reproduction commit link:** https://github.com/VincentTLe/pathreview/commit/f0358585adf3cd6d6164526b5d226c234440505b

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

**PLAN.md link:** https://github.com/VincentTLe/pathreview/blob/fix/150-tech-detector-vendored-files/PLAN.md

**Walkthrough video (recommended):** _(optional — not recorded; not graded)_

**Blockers or open questions:**
Keeping the Week 9 fix scoped to the vendored/build exclusion. The separate
`sorted(languages)[0]` "primary = alphabetical, not most-common" behavior is a
real but distinct bug; leaning toward raising it as a follow-up rather than
expanding this Tier-1 PR.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The fix is implemented and pushed
([`fbeb3e4`](https://github.com/VincentTLe/pathreview/commit/fbeb3e4)).
Sub-tasks from PLAN.md that are done:

- Rewrote `_should_skip_file()` to match **path segments** instead of
  slash-wrapped substrings — normalize `\` → `/`, split on `/`, and skip the
  file when any segment is a known vendored/build directory.
- Added the directory names as a class-level `SKIP_DIRS` frozenset.
- Added regression tests in a new file
  `tests/unit/test_tech_detector_vendored.py` (root-level, nested,
  Windows-separator, and look-alike cases).
- Verified: the two pre-existing tests `test_node_modules_excluded` and
  `test_build_directory_excluded` now pass, and the full unit suite went from
  **53 failed / 375 passed** (baseline, before my change) to **51 failed /
  382 passed** — i.e. my two target tests fixed, five new tests added, and no
  new failures introduced. The remaining 51 failures are pre-existing and
  belong to other issues.

**Next steps:**
Open a draft PR and request peer/mentor feedback in Slack; address any feedback;
fill in Check-in 2 with the PR link and mark the PR ready for review.

**Blockers:**
None. Note: `make check` and `make test-unit` have extensive pre-existing
failures across the repo (182 ruff findings, 52 unformatted files, and 53
failing unit tests before my change) that are unrelated to issue #150; my change
keeps its edited files lint/format/type clean and introduces no new test
failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/959

**Branch:** `fix/150-tech-detector-vendored-files`

**What you built:**
`TechDetector` now excludes vendored dependencies and build output before
counting languages, by matching each path segment against a `SKIP_DIRS` set, so
the reported primary language reflects first-party source instead of bundled
JavaScript.

**Tests added or updated:**
Added `tests/unit/test_tech_detector_vendored.py` (5 tests: root-level vendor
and node_modules exclusion, Windows-separator build output, nested vendored
dirs, and look-alike names that must not be skipped). The change also turns the
existing `test_node_modules_excluded` and `test_build_directory_excluded` green.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

_"Passes" here means my changes introduce no new failures: my edited files are
ruff/black/mypy-clean (verified by the pre-commit hooks on the fix commit), and
`make test-unit` went from 53 failed / 375 passed (baseline) to 51 failed / 382
passed — the two target tests fixed and five new tests added, no new failures.
The repo's remaining pre-existing lint/type/test failures are unrelated to #150._

**Draft PR feedback received from:** none yet — draft PR shared in the cohort
Slack; no responses at the time of writing.
