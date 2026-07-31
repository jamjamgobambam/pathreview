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

**Reproduction commit link:** https://github.com/faisalkhansk3283/pathreview/commit/69bb0658eba950df6e28147c80e90e1862433ab0

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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented segment-based path matching in `_should_skip_file()`
(`agent/tools/tech_detector.py`), replacing the broken slash-wrapped substring check that
required a leading `/` and therefore missed repo-root-relative vendor/build paths. All 28
tests in `tests/unit/test_tech_detector.py` pass, including the two named in the issue
(`test_node_modules_excluded`, `test_build_directory_excluded`) plus a new test I added
(`test_filename_containing_skip_word_not_excluded`) guarding against false-positive substring
matches (e.g. `vendor_utils.py` incorrectly being treated as vendored). Confirmed via
`git stash` comparison that the `make check` (182 errors) and `make test-unit` (51 failures)
issues are pre-existing on `main` and unrelated to this change — none touch
`tech_detector.py` or `test_tech_detector.py`.

**Next steps:**
Open a draft PR, request peer/mentor review in Slack, address feedback, then finalize and
submit for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [ADD AFTER OPENING PR]

**Branch:** fix/150-vendored-build-output-detection

**What you built:**
Fixed `TechDetector._should_skip_file()` in `agent/tools/tech_detector.py` so vendor/build
directories (`node_modules/`, `build/`, `vendor/`, etc.) are excluded from language detection
even when they appear at the repo root. The fix splits each file path into `/`-separated
segments and checks for an exact segment match against a set of skip-directory names, instead
of the old approach of checking for a fixed `/name/`-wrapped substring, which silently failed
for root-relative paths.

**Tests added or updated:**
`tests/unit/test_tech_detector.py` — confirmed the two existing tests named in the issue
(`test_node_modules_excluded`, `test_build_directory_excluded`) now pass, and added
`test_filename_containing_skip_word_not_excluded` to guard against false-positive substring
matches (e.g. `vendor_utils.py`).

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [ADD AFTER REVIEW]
