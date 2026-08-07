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

**PR link:** https://github.com/ascherj/pathreview/pull/443

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

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both commands report pre-existing failures unrelated to this change — 181 lint errors and 51
test failures, confirmed identical on `main` via `git stash` comparison. My change introduces
no new failures.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in on PR #443. Per the Su26 program note, reviewer feedback is not a feature
this term, so this was expected rather than a sign of a problem with the PR itself.

**How you responded:**
N/A — nothing to respond to. I kept the PR open and marked ready for review in case a
maintainer picks it up later.

---

### Reflection

**What was harder than you expected?**
Git itself, more than the actual code fix. The bug fix in `tech_detector.py` was
straightforward once I understood the root cause, but I ran into a branch divergence when
pushing my Week 8 commits — my local branch and the remote branch had each picked up
different commits since I last synced, so a plain `git push` was rejected. I had to learn
`git stash` (temporarily shelving uncommitted local changes so they don't block other git
commands, then restoring them later with `git stash pop`) and `git rebase` (replaying my
commits on top of the remote's latest commit to keep history linear, instead of creating a
merge commit) practically for the first time, including resolving a real merge conflict in
`JOURNAL.md` by hand. Going in, I didn't have a mental model for any of this — I could run
`git add`/`commit`/`push` fine, but branch divergence and conflicts were new territory.

**What did you learn about working in a large codebase?**
In my own projects, I can hold the whole thing in my head and understand my code by just
looking at it. In `pathreview`, understanding `tech_detector.py` wasn't enough — I also had
to understand the project's existing test conventions before adding a new test, respect
`CONTRIBUTING.md`'s commit/branch naming rules, and deal with `make check`/`make test-unit`
surfacing 181 lint errors and 51 test failures across files I never touched. A big part of
contributing to a large codebase is learning to distinguish "this is broken because of my
change" from "this was already broken and isn't my problem" — and proving that distinction
with evidence (like comparing `main` against my branch) rather than just asserting it.

**How did AI tools help — and where did they fall short?**
AI tools worked well as a pair programmer — pointing me to the exact file and line for the
bug, helping me reason through why my first instinct (a plain substring check like `"vendor"
in filepath`) would cause false positives, and drafting boilerplate like the PLAN.md sections
and PR description so I could focus on the actual logic. Where it fell short was git
mechanics — reading a set of stash/rebase instructions and actually understanding what was
happening to my repo were two different things, and I had to ask for a plain-language
explanation of stash and rebase separately before it really clicked, rather than just
following commands blindly.

**What would you do differently if you started over?**
I'd spend more time upfront getting comfortable with git branching and conflict resolution
before starting the issue itself, instead of learning it under pressure mid-week when my
push got rejected. I'd also practice on more issues going forward to build the muscle memory
for the full contribution cycle end-to-end, so branch divergence and conflicts feel routine
instead of stressful, with the eventual goal of getting a PR actually merged.

**What are you most proud of from this module?**
Getting comfortable running a real production-scale codebase locally — setting up the venv,
diagnosing dependency and permission issues, running the actual test suite, and using that
environment to reproduce and fix a real bug — rather than just reading code in isolation.
That hands-on ability to spin up, inspect, and modify a codebase I didn't write is the part
I want to keep building on.
