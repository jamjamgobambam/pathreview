# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `tech_detector` agent tool guesses a repository's primary language by
scanning file extensions, and it is supposed to ignore third-party and
generated code (things under `node_modules/`, `build/`, `vendor/`, etc.). The
skip logic lives in `agent/tools/tech_detector.py`, but every skip pattern is
written with a leading slash (`/node_modules/`, `/build/`), so it only matches
those directories when they are nested inside another folder. When a vendored
or build directory sits at the repository root — which is the normal case —
its root-relative path has no leading slash, nothing gets excluded, and the
bundled JavaScript files outnumber the real source. A repo with 2 Python files
and 6 vendored JS files is then reported as "JavaScript." A successful fix makes
the exclusion match root-level directories too, so vendored/build files are
dropped before language counting and the reported primary language reflects the
actual source (e.g. Python). The two previously failing tests,
`test_node_modules_excluded` and `test_build_directory_excluded`, should pass.

**Branch name:** fix/150-exclude-vendored-build-files

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### Selection notes — "Is this right for me?" checklist

- **Scope is small and localized.** The bug lives in a single helper,
  `TechDetector._should_skip_file`, in one file
  (`agent/tools/tech_detector.py`). No cross-module changes are needed.
- **The problem is clearly reproducible.** The issue ships an exact repro, and
  it fails deterministically before the fix and passes after.
- **Tests already exist.** `tests/unit/test_tech_detector.py` includes
  `test_node_modules_excluded` and `test_build_directory_excluded` that encode
  the expected behavior, so I have a built-in definition of "done."
- **I understand the root cause.** It is a path-matching bug: skip patterns
  require a leading slash, so root-level vendored/build directories never match.
- **Low risk of scope creep.** I noted a separate latent issue (primary language
  is chosen alphabetically from a set rather than by file count), but it is out
  of scope for #150 and all existing tests pass without touching it.

Conclusion: good Tier 1 fit for a first contribution to this codebase.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/paulshao2698/pathreview/commit/e6d680f3757dc5de248da2d5f73909f093448ed2

**Reproduction summary:**
I ran the exact file list from the issue through `TechDetector` in my local
venv and against the base (pre-fix) code it reported `primary_language ==
"JavaScript"` — the 6 vendored `node_modules/`/`build/` `.js` files outvoted
the 2 real `.py` files. I also confirmed it by running the repo's own tests
against the pre-fix code: `test_node_modules_excluded` and
`test_build_directory_excluded` both fail with `AssertionError: assert
'JavaScript' == 'Python'` (`2 failed, 25 deselected`). The reproduction is
scripted in `repro_issue_150.py`.

**PLAN.md link:** https://github.com/paulshao2698/pathreview/blob/fix/150-exclude-vendored-build-files/PLAN.md

**Walkthrough video (recommended):** Not recorded (optional / not graded).

**Blockers or open questions:**
- The `.venv` is Python 3.14; a couple of backend dependencies may lack 3.14
  wheels, which could affect running the full app (frontend at :5173 already
  runs; backend + Docker DB still to be brought up). Does not block the #150
  Python fix, which is verified by the unit tests.
- Noted but out of scope: `primary_language` is documented as "most common" but
  is actually the alphabetically-first entry of a set (occurrences are never
  counted). Leaving this untouched for #150 — flagging in case a follow-up
  issue is warranted.
