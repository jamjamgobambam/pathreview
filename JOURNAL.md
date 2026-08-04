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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Omarhus01/pathreview/commit/cab0279

**Reproduction summary:**
Ran `pytest tests/unit/test_tech_detector.py -k "test_node_modules_excluded or test_build_directory_excluded" -v`
against the unmodified code. Both tests fail with
`AssertionError: assert 'JavaScript' == 'Python'`, confirming that
`_should_skip_file`'s leading-slash patterns (e.g. `"/node_modules/"`) never
match the leading-slash-free relative paths the tool actually receives, so
vendored `.js` files leak into the language count. Documented the root
cause as a comment at the buggy check in `agent/tools/tech_detector.py`
(no fix applied yet).

**PLAN.md link:** https://github.com/Omarhus01/pathreview/blob/fix/150-tech-detector-vendor-build-files/PLAN.md

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
While reproducing, noticed `primary_language` is actually chosen as
`sorted(languages)[0]` (alphabetically first), not by file-count frequency
as the issue description implies. The two pinned tests still pass once
filtering is fixed because filtering correctly leaves only `{"Python"}` in
both cases, so I don't think this needs a separate fix for #150 — flagging
it in PLAN.md's Risks section and will call it out in the PR description
rather than silently expanding scope. Also noting for Week 9: a full
`pytest tests/unit -m unit` run currently shows 53 pre-existing failures
unrelated to this issue (only 2 belong to #150) — will re-confirm that
count doesn't grow after the fix.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md step 2: `_should_skip_file` in
`agent/tools/tech_detector.py` now normalizes `filepath` with a leading `/`
before matching skip patterns, so root-level vendor/build paths (e.g.
`node_modules/pkg/index.js`) match the same way nested ones already did.
`test_node_modules_excluded` and `test_build_directory_excluded` both pass
now. Also completed PLAN.md steps 3–4: tightened the weak tests in
`test_tech_detector.py` that exercised the code with no `assert`
(`test_vendor_files_excluded`, `test_dockerfile_detection`,
`test_github_actions_detection`, `test_makefile_detection`,
`test_framework_detection`, `test_cpp_detection`, and
`test_ipynb_counted_as_python_not_json`), and added a new
`test_nested_vendor_directory_excluded` regression test for the
nested-vendor-directory edge case called out in PLAN.md's Risks section.
File now stands at 28/28 passing.

**Next steps:**
Run the full `make check` / `make test-unit` suite and diff against the
Week 8 baseline (53 failed / 375 passed) to confirm the fix removes exactly
the 2 pinned failures and introduces nothing new (PLAN.md step 5). Then
write the PR description and open the PR against `ascherj/pathreview:main`.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/TBD

**Branch:** `fix/150-tech-detector-vendor-build-files`

**What you built:**
Fixed `_should_skip_file` in `agent/tools/tech_detector.py` so vendor/build
directory patterns (`node_modules/`, `vendor/`, `dist/`, `build/`, etc.)
match repo-relative paths regardless of leading slash, by anchoring the
filepath with `/` before the existing substring check. This stops vendored
JS files from being counted as source, so `primary_language` correctly
reports `"Python"` for a repo with only vendored/build JS alongside real
Python files.

**Tests added or updated:**
`tests/unit/test_tech_detector.py` — tightened six existing tests that
previously called `detector.execute()` with no assertion
(`test_vendor_files_excluded`, `test_dockerfile_detection`,
`test_github_actions_detection`, `test_makefile_detection`,
`test_framework_detection`, `test_cpp_detection`), rewrote
`test_ipynb_counted_as_python_not_json` to assert directly instead of
computing an unused variable, and added `test_nested_vendor_directory_excluded`
to cover a vendor directory nested below the repo root. 28/28 tests in the
file pass; a full `pytest tests/unit -m unit` run is 51 failed / 378 passed,
down from the Week 8 baseline of 53 failed / 375 passed — diffing the two
failure lists confirms only the two #150 tests moved from fail to pass and
nothing else changed.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(both scoped to "no new failures introduced" — `ruff`/`black`/`mypy` are
clean on the two changed files; the repo-wide pre-existing failures noted
in Week 8 and above are unaffected by this change and documented in the PR
description.)

**Draft PR feedback received from:** none — per this term's format there is
no reviewer feedback loop; self-reviewed against the Week 9 "seven
conditions for done" instead.
