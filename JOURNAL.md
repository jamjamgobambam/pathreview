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

**Cohort ledger:** [x] Issue added to cohort ledger

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

**PR link:** https://github.com/ascherj/pathreview/pull/418

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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments came in on PR #418 during the module. (Per the
Summer 2026 course note, reviewer feedback isn't an active feature this cohort.) I
checked the PR conversation on GitHub — reviews and comments were both empty, status
`OPEN` / `REVIEW_REQUIRED` — so there was nothing to respond to.

**How you responded:**
Nothing to respond to yet. The PR is open and ready for review if the maintainer
picks it up later.

---

### Reflection

**What was harder than you expected?**
Trusting that a broken codebase wasn't my fault. When I ran `make test-unit` I got
51 failing tests and `make check` threw 181 lint errors, and my gut reaction was "I
broke everything." The harder skill wasn't fixing my bug — it was proving those
failures were *pre-existing* by checking out a clean `main` and running the same
commands there, so I could confidently write in the PR "my change introduces zero new
failures." Separating my blast radius from the codebase's existing mess took more care
than the actual fix.

**What did you learn about working in a large codebase?**
In my own projects I know where everything is, so if something's broken it's on me.
Here, most of what was "wrong" had nothing to do with me — other people's half-finished
issues, unrelated modules. Contributing to someone else's production code is mostly
*discipline about scope*: touch only the file the issue names (`tech_detector.py`),
match their existing conventions (branch naming, commit format, docstring style, the
pre-commit hooks), and prove you didn't make things worse rather than trying to fix the
whole repo. I actually found a *second* bug while I was in there (the primary-language
picker uses `sorted()[0]`, so it returns the alphabetically-first language instead of
the most common) — and the discipline was choosing NOT to fix it, because it was out of
scope for issue #150, and instead noting it for a follow-up.

**How did AI tools help — and where did they fall short?**
AI was strongest at *navigation and speed*: tracing the bug from the issue down to the
exact line, explaining why leading-slash substring matching silently fails on top-level
paths, and drafting the segment-matching rewrite plus the docstring in the project's
style. It was also great at grunt work — running the test suite, capturing the
before/after output, and drafting the PR description. Where it fell short: it couldn't
make the *judgment calls* for me. Deciding the scope boundary (fix the vendored-dir bug,
leave the `sorted()[0]` bug alone), deciding this was a real reproduction and not a fluke,
and the accountability stuff — submitting the right branch URL, claiming the issue,
requesting a regrade when a different project got mis-graded — all of that is on me. AI
hands you the code; it doesn't own the contribution.

**What would you do differently if you started over?**
Be religious about *how* I submit, not just *what* I build. On an earlier project I lost
points because a submission link pointed a grader at `main` (the starter code) instead of
my feature branch — all my real work was one branch away and invisible. That burned in a
lesson I carried through all four weeks here: always submit the `/tree/<branch>` URL, never
a bare repo link. I'd also open the PR even earlier than I did — the assignment kept saying
"don't wait for the deadline," and having it open early is the only way real feedback can
reach you in time.

**What are you most proud of from this module?**
Not the code itself — it's a small, clean fix — but that the whole contribution is
*honest and self-documenting*. Anyone can open PR #418 and see exactly what broke, a
reproduction with real before/after output, an upfront note that the codebase's 51
pre-existing failures aren't mine, and even a flagged second bug I chose to leave for a
follow-up. That's what a real open-source contribution looks like, and it reads like I
actually understood the code instead of just making tests go green.

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
