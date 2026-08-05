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

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `TechDetector._should_skip_file`
(`agent/tools/tech_detector.py`): normalize Windows separators to `/` and
prepend a leading `/` before matching, so root-level vendored/build directories
are excluded like nested ones. PLAN.md sub-tasks 1–3 are done. Added two unit
tests (Windows separators, skip-token false positive); the full
`tests/unit/test_tech_detector.py` suite is green (29 passed), including the two
tests that were failing pre-fix.

**Next steps:**
Run scoped `ruff`/`black`/`mypy` on the touched files, write the PR description
from the repo template, open a draft PR, and request peer review in Slack.

**Blockers:**
Running the full `make check` / `make test-unit` requires the complete backend
dependency set (`make setup`), and the local venv is Python 3.14, where some
heavy deps (chromadb, tiktoken) may lack wheels. Verified my change is clean in
isolation instead (see Check-in 2). Not a blocker for the #150 fix.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/362

**Branch:** `fix/150-exclude-vendored-build-files`

**What you built:**
The tech detector's skip logic matched vendored/build directories only when
they were nested (patterns used a leading slash, e.g. `/node_modules/`), so
root-level `node_modules/` and `build/` — the normal case — were never excluded
and bundled JS skewed the detected language. The fix normalizes each path
(backslashes → `/`, plus a prepended leading `/`) before the substring match, so
root-level and Windows-style paths are excluded consistently.

**Tests added or updated:**
`tests/unit/test_tech_detector.py` — added `test_windows_separators_excluded`
and `test_source_file_containing_skip_token_not_excluded`. The pre-existing
`test_node_modules_excluded` and `test_build_directory_excluded` (which failed
before the fix) now pass. Full file: 29 passed.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> Per the "pre-existing failures" guidance: "passes" here means my change
> introduces **no new failures**, not that the whole repo is clean. Documented
> pre-existing state below.

**Pre-existing failures (unrelated to this change):**
- `ruff check .` reports 182 errors repo-wide; `black --check .` would reformat
  52 files. In the files I touched, the counts are identical before and after my
  change: `tech_detector.py` has 1 pre-existing ruff error (import ordering) and
  pre-existing black formatting in `execute()`/`_detect_tech()` (code I did not
  modify); `test_tech_detector.py` has 8 pre-existing `F841` unused-variable
  errors in other tests. My added lines are clean under `ruff`, `black`, and
  `mypy` (`mypy agent/tools/tech_detector.py` → success).
- `make test-unit` cannot collect 9 test modules locally because backend deps
  (e.g. `tiktoken`) aren't installed in this venv; this is an environment gap,
  not a code failure. The module relevant to my change collects and passes (29).
- I left the pre-existing lint/format debt untouched to keep the diff minimal
  and scoped to #150, per "don't fix the entire codebase."

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No maintainer/reviewer comments came in on PR #362. Per the Summer 2026 course
note, reviewer feedback on the PR is not a feature this term, so none was
expected. (The only feedback I received was course grading feedback, which
reviewed the whole PathReview codebase rather than my PR's diff — none of it
identified an issue in the files my change actually touched.)

**How you responded:**
No PR review to respond to. On the grading feedback that critiqued unrelated
base-code files (e.g. `review_service.py`, `ingestion/pipeline.py`), I confirmed
those files were not in my diff and intentionally kept my PR scoped to #150
rather than absorbing unrelated changes.

---

### Reflection

**What was harder than you expected?**
The process was far harder than the code. The fix itself was a few lines. What
tripped me up repeatedly was submission mechanics: I was graded 0 — twice — with
"no JOURNAL.md found," even though every artifact was committed and pushed. The
grader kept resolving my submission to the `main` branch, where none of my work
lived; all of it was on my feature branch. The instructions warned about
submitting the `/tree/<branch>` URL instead of a bare repo link on every single
page, and I still hit it. The lesson landed hard: being correct is worthless if
the reviewer can't see your work.

**What did you learn about working in a large codebase?**
Contributing to someone else's production code is a discipline of restraint, not
just capability. On my own projects I fix whatever I notice. Here, the right move
was the opposite: keep the diff minimal, touch only what the issue requires, and
resist "while I'm in here" changes. When I found a second latent bug (the primary
language is chosen alphabetically instead of by file count) and when the codebase
had 182 pre-existing ruff errors, the professional response was to document them
and leave them alone — not to expand my PR. I also learned to read the real code
before trusting any summary of it: the root cause here (leading-slash patterns
missing root-level paths) was invisible from the issue description alone and only
obvious once I traced `_should_skip_file` directly.

**How did AI tools help — and where did they fall short?**
AI was strongest at navigation and mechanics: locating `_should_skip_file`,
tracing the code path, generating a genuine before/after reproduction (running
the pre-fix code to capture the `JavaScript` result and the two failing tests),
drafting tests that matched existing patterns, and structuring PLAN.md, the PR
description, and these journal entries. Where it fell short was anything outside
the repo or requiring my judgment and credentials: it couldn't run the GitHub
auth flow or click "submit," couldn't stand up the full backend (Docker/Node
weren't installed and the venv was Python 3.14, where some deps lacked wheels),
and — tellingly — it flagged the `/tree/<branch>` requirement repeatedly but
couldn't stop me from submitting the wrong link, because that step was mine to
own. AI accelerated the work; it did not remove responsibility for verifying the
result from the reviewer's point of view.

**What would you do differently if you started over?**
Three things. First, stand up the full environment end-to-end before touching
code — I got the frontend running but never fully brought up the backend, which
limited how I could verify. Second, verify every submission from the grader's
point of view: open the exact link I'm about to submit and confirm it shows my
JOURNAL.md before hitting send. That one habit would have saved two zeros.
Third, file the latent alphabetical-primary-language bug as its own follow-up
issue immediately, so it's captured rather than just noted in a journal.

**What are you most proud of from this module?**
That I can explain every decision in this contribution — not just what the fix
does, but why it's scoped the way it is, why I left the pre-existing debt alone,
and how I proved the bug was real before I changed anything. The reproduction
discipline especially: I didn't just assert the bug existed, I ran the pre-fix
code and captured the two tests failing with `assert 'JavaScript' == 'Python'`,
so the problem was demonstrated, not assumed.

