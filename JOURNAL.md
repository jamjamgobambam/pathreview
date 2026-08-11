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

**PR link:** https://github.com/ascherj/pathreview/pull/984

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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
Checked PR #984 (https://github.com/ascherj/pathreview/pull/984) as of
2026-08-11: still open, no comments, no reviews, no assignees. Consistent
with the Su26 note that reviewer feedback isn't part of this term's format.

**How you responded:**
N/A — nothing to respond to. Re-read my own PR description once more
against `docs/CONTRIBUTING.md` to confirm it still accurately describes the
change (it does: the fix, the two tightened/added tests, the 53→51 failure
diff, and the alphabetical-`primary_language` note are all still current).

---

### Reflection

**What was harder than you expected?**
Not the fix itself — `_should_skip_file` was a five-line change once I'd
actually traced the bug. The hard part was staying honest about what
*counted* as the fix. Two things kept trying to pull scope wider: the
alphabetical-vs-frequency `primary_language` quirk I found while reading
`_detect_tech` (PLAN.md Risks), and the six pre-existing tests in
`test_tech_detector.py` that called `.execute()` with no `assert` at all.
Both were legitimately adjacent to the bug I was fixing, and both were
tempting to "just fix while I'm in here." Deciding where the line was —
document the alphabetical quirk in the PR description but don't touch it;
tighten the assertion-less tests because they directly covered the code
path I was changing, but not touch unrelated failing test files — took more
judgment than the actual code change did.

**What did you learn about working in a large codebase?**
That "tests pass" isn't a meaningful signal on its own in a codebase you
don't own — you need a baseline. The full `pytest tests/unit -m unit` suite
had 53 pre-existing failures before I touched anything, spread across
modules I never went near (`test_review_service.py`, `test_resume_parser.py`,
etc.). If I'd just run the suite after my change and seen "51 failed" I
couldn't have told you whether that was progress or a new regression hiding
behind an unrelated fixed flake. Recording the Week 8 baseline and diffing
the actual failure *lists* (not just counts) after the fix was the only way
to make a real claim in the PR description. I also learned to `grep` for
every caller of a function before changing it (`_should_skip_file`,
`TechDetector`) rather than trusting that a change confined to one function
stays confined in its effects — in someone else's production code, "this
looks self-contained" is a hypothesis to check, not a fact.

**How did AI tools help — and where did they fall short?**
Most useful for the mechanical, high-recall work: grepping the codebase for
every reference to `_should_skip_file`/`TechDetector` to confirm blast
radius, drafting the edge-case list in PLAN.md (nested vendor dirs, exact
directory-name matches, path position), and keeping PLAN.md/JOURNAL.md
consistent with each other as the branch moved forward. It fell short on
the two judgment calls that mattered most: whether the alphabetical
`primary_language` selection was in-scope for #150, and whether tightening
the six weak tests counted as "fixing the issue" or "unrelated cleanup." AI
suggestions leaned toward fixing everything adjacent that looked broken;
the actual scoping decision — and the accompanying honesty in the PR
description about what was *not* fixed — had to be mine.

**What would you do differently if you started over?**
I'd run the full-suite baseline diff in Week 7, at issue-selection time,
instead of Week 8. Knowing upfront that the repo already had 53 unrelated
failures would have saved a moment of doubt in Week 9 when my local run
showed failures after my change — I had to go back and re-confirm against
the Week 8 numbers instead of already having them in hand. I'd also timebox
the `primary_language` tangent explicitly instead of open-endedly reading
`_detect_tech` — it was worth the twenty minutes it took, but I got there by
curiosity rather than a planned check.

**What are you most proud of from this module?**
Catching that the issue's own description was subtly wrong — it frames the
bug as vendored files being over-*counted* by frequency, but `primary` was
never frequency-based, it's `sorted(languages)[0]`. It would have been easy
to accept the issue text at face value, ship a fix that made the two pinned
tests pass, and move on without noticing the discrepancy. Reading the code
closely enough to catch that, then choosing to document it rather than
silently "fix" a second bug nobody asked for, is the part of this module I
think best reflects how I'd want to work on a real team.
