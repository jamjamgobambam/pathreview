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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ATgzh/pathreview/commit/ff23b0fc64d98ec3271e397dc32adbdeccee407c

**Reproduction summary:**
Wrote `scripts/repro_issue_150.py`, a runnable script using the exact file
list from the issue body (2 Python files, 6 vendored/build JS files). Running
it against current `main` confirms the bug directly: `primary_language`
comes back `"JavaScript"` instead of the expected `"Python"`, because
`_should_skip_file`'s leading-slash-anchored patterns never match top-level
paths like `node_modules/lib/index.js`. This matches the two pre-existing
failing tests named in the issue (`test_node_modules_excluded`,
`test_build_directory_excluded`), which I also reran and confirmed still
fail against `main`.

**PLAN.md link:** https://github.com/ATgzh/pathreview/blob/fix/150-tech-detector-vendored-files/PLAN.md

**Walkthrough video (recommended):** Not recorded — I don't have a screen
recording tool available in this environment. Skipping it since it's
explicitly not graded; happy to record one later if it'd help for office
hours.

**Blockers or open questions:**
None blocking. Two things I'm carrying into Week 9: (1) I haven't seen the
"strong vs. weak solution plans" example doc referenced in the Week 8
resources — no URL was available to me — so I can't confirm PLAN.md matches
the expected level of detail beyond following the template structure
carefully; would appreciate a gut-check. (2) My planned fix (splitting paths
into segments and matching directory components) is a slightly different
approach than a minimal patch to the existing regex-like patterns — I think
segment-matching is more correct (see Risks & unknowns in PLAN.md for why),
but I'll keep it small and reversible if reviewers prefer the narrower diff.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md are implemented. `_should_skip_file` in
`agent/tools/tech_detector.py` now splits each path on `/` and checks the
directory segments (every part except the filename) against a skip-dir set,
instead of substring-matching slash-anchored patterns — this is the fix
described in PLAN.md's Plan section, step 1. `test_node_modules_excluded`
and `test_build_directory_excluded` pass now. I added a real assertion to
`test_vendor_files_excluded` (step 3) and 4 new tests exercising
`_should_skip_file` directly for the edge cases from PLAN.md: root-level
dirs, nested dirs, a file whose name collides with a skip-dir name, and
substring-vs-exact matching (`rebuild/` must not match `build`). Reran
`scripts/repro_issue_150.py` (step 4) — it now prints "Not reproduced." Ran
`make test-unit` and `make check` (step 5) and confirmed no new failures
against the baseline I captured before touching anything: test-unit went
from 53 failed/375 passed to 51 failed/381 passed (the 2 fewer failures are
the two tests this issue's fix resolves; the 4 more passing are my new
tests); ruff went from 182 to 173 pre-existing errors repo-wide (fixed 9 in
files I was already touching, introduced 0 new); black and mypy counts are
otherwise unchanged. Full breakdown is in the PR description.

Along the way I hit a real blocker: the local pre-commit `mypy` hook has no
path filter, so it checks every staged Python file — including `tests/`,
which the project's own `Makefile`/CI explicitly exclude from typechecking.
That mismatch blocked any commit touching a test file (repo-wide, not just
mine — the whole test suite fails this hook). I fixed the hook's scope in
`.pre-commit-config.yaml` to match the Makefile/CI paths, and separately
cleaned up 7 pre-existing unused-variable lint errors in
`test_tech_detector.py` that were blocking the ruff hook the same way. Both
are documented in the same commit as clearly-labeled, separate concerns from
the actual fix.

**Next steps:**
Open a PR against the upstream repo, fill in the PR template completely
(including the pre-existing-failures note above), and get it in front of a
classmate or mentor in Slack for draft feedback before marking it ready for
review.

**Blockers:**
None on the implementation. Opening the actual PR and getting peer/mentor
review both require steps outside what I can do unassisted — pending
confirmation to open the PR, and the Slack review itself is a human-in-the-
loop step I can't complete on my own.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/753 — **currently a
draft**, opened to request peer/mentor feedback in Slack before finalizing.
Still needs to be marked "Ready for review" before the deadline; this is not
yet the final submission state.

**Branch:** `fix/150-tech-detector-vendored-files`

**What you built:**
Fixed `TechDetector._should_skip_file` in `agent/tools/tech_detector.py` so
it matches vendored/build directories (`node_modules`, `vendor`, `dist`,
`build`, `.git`, `__pycache__`, `.venv`, `venv`) by exact path segment
instead of a slash-anchored substring — this catches root-level paths like
`node_modules/lib/index.js` that the old substring check missed, while
keeping already-working nested paths (`src/vendor/lib.js`) working and
avoiding a false positive for a file whose name merely matches a skip-dir
name.

**Tests added or updated:**
`tests/unit/test_tech_detector.py` — added a real assertion to
`test_vendor_files_excluded` (previously asserted nothing), and added 4 new
tests exercising `_should_skip_file` directly (root-level dirs, nested dirs,
filename/directory-name collision, substring-vs-exact matching). Also
cleaned up 7 pre-existing unused-variable lint errors elsewhere in the same
file that were blocking any commit touching it (documented as a separate
concern in the commit message and PR description, not part of the #150
fix itself).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
— in the "introduces no new failures" sense defined by this week's
instructions: baseline captured before any change (53 failed/375 passed on
test-unit, 182 ruff errors, 52 files needing black, 99 mypy errors) vs. after
(51 failed/381 passed, 173 ruff errors, 51 files needing black, 99 mypy
errors unchanged) — every number improved or stayed flat, none regressed.
Full table is in the PR description. Neither command exits zero overall,
because of pre-existing repo-wide issues outside files this PR touches.

**Draft PR feedback received from:** none yet — PR was just opened as a
draft; posting it in Slack for review is my next step.

**Draft PR feedback received from:** _pending_
