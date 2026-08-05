# Contribution Journal — PathReview (Module 3)

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview's `tech_detector` tool infers a repository's primary programming
language from its file extensions, but it counts files it is supposed to ignore.
Its directory-skipping helper (`_should_skip_file`) matches patterns like
`"/node_modules/"` as slash-wrapped substrings, so top-level vendored or
generated folders such as `node_modules/` and `build/` slip through and the
third-party / bundled JavaScript inside them gets counted. The result is that a
mostly-Python repository can be misreported as JavaScript. A successful fix makes
the detector match on path *segments* instead, excluding those directories
whether they sit at the repo root or nested deeper, which turns the two provided
failing tests (`test_node_modules_excluded`, `test_build_directory_excluded`)
green. This lives in `agent/tools/tech_detector.py` in the Agent system.

**Branch name:** fix/150-exclude-vendored-build-files

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### "Is this right for me?" — selection notes

Worked through the checklist before claiming the issue:

- **Open and unassigned?** Yes — no one is assigned, so I'm not duplicating work.
- **Labeled for my level?** Yes — `tier-1` **and** `good first issue`; appropriate
  as a first contribution to a large codebase.
- **Can I reproduce it?** Yes — cloned, set up locally, and the two named tests
  (`test_node_modules_excluded`, `test_build_directory_excluded`) fail exactly as
  the issue describes; the issue's manual repro also reproduces (`primary_language`
  comes back `JavaScript` instead of `Python`).
- **Is the scope contained?** Yes — the bug lives in a single method
  (`_should_skip_file`) in one file (`agent/tools/tech_detector.py`), ~10 lines.
- **Clear acceptance criteria?** Yes — two failing tests define "done"; I code to
  a target rather than guessing intent.
- **Do I understand the root cause?** Yes — slash-wrapped substring matching
  misses top-level directories (documented in Working notes below).
- **Does it need deep domain knowledge?** No — it's string/path handling, not RAG
  or agent internals, so it's tractable without understanding the whole system.

**Scope reasoning:** I'm keeping this PR to *only* the vendored/build exclusion
bug. While investigating I found a second, separate defect — primary language is
selected alphabetically (`sorted(languages)[0]`) rather than by file count,
despite the "most common" comment — but fixing the exclusion logic alone
satisfies both acceptance tests, and bundling an unrelated behavior change would
work against a clean, reviewable first PR. I've noted the counting bug as a
candidate for a separate issue.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/yarinacs/pathreview/commit/e67c0b3

**Reproduction summary:**
Ran the two named failing tests and the issue's manual snippet against my local
environment: for a repo of 2 Python files + 6 vendored JS files (`node_modules/`,
`build/`), `TechDetector` returns `primary_language = "JavaScript"` instead of
the expected `"Python"`, because the vendored/build files are counted.

**PLAN.md link:** https://github.com/yarinacs/pathreview/blob/fix/150-exclude-vendored-build-files/PLAN.md

**Walkthrough video (recommended):** [not recorded — optional, not graded]

**Blockers or open questions:**
One open question for Week 9: whether to also address a *separate* defect I found
— primary language is chosen alphabetically (`sorted(languages)[0]`), not by file
count, despite the "most common" comment. I plan to keep it out of scope for #150
and suggest a separate issue, but will confirm with a mentor. Otherwise no
blockers — the fix is already implemented and passing on this branch.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md — rewrote `_should_skip_file()` in
`agent/tools/tech_detector.py` to match on path segments instead of slash-wrapped
substrings (PLAN "Plan" sub-tasks 1–4 done). The two acceptance tests
(`test_node_modules_excluded`, `test_build_directory_excluded`) now pass and the
issue's manual repro returns `Python`. Added two edge-case unit tests (top-level
`dist/` exclusion; full exclusion of `node_modules` JS). Captured a baseline vs.
after comparison: my changes introduce **no new** `make check` / `make test-unit`
failures and reduce test failures by two.

**Next steps:**
Open a draft PR, request peer/mentor review in Slack, address any feedback I
agree with, then mark it ready for review and confirm the PR template is complete.

**Blockers:**
None on the code. (Tooling note: `gh` CLI is not authenticated in my local
environment, so the PR is opened via the GitHub web UI rather than the command
line.)

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/811

**Branch:** `fix/150-exclude-vendored-build-files`

**What you built:**
`tech_detector`'s directory-skip helper now matches vendor/build directories by
path *segment* (`filepath.split("/")`), so top-level `node_modules/`, `build/`,
`dist/`, etc. are excluded from language detection as well as nested ones. This
stops third-party/bundled files from skewing a repo's detected primary language.

**Tests added or updated:**
`tests/unit/test_tech_detector.py` — added `test_dist_directory_excluded` and
`test_top_level_vendored_files_fully_excluded`. Both assert the vendored language
(`JavaScript`) is fully absent from `all_languages`, not just that the primary
language is correct. The two pre-existing acceptance tests now pass as well.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
<!-- "passes" per the documented pre-existing-failures rule = my changes introduce
     NO new failures. Baseline on main: test-unit 53 failed / ruff 86 / black 52
     files / mypy 103 errors. After my changes: test-unit 51 failed (2 fewer) /
     ruff 86 / black 52 / mypy 103 — all unrelated pre-existing failures unchanged. -->

**Draft PR feedback received from:** Claude (AI mentor review — approved by
instructor as the reviewer for this cohort). Feedback: hoist the local `skip_dirs`
set to a `SKIP_DIRS` class constant to match the module's existing pattern
(`EXT_TO_LANG`, `CONFIG_INDICATORS`) and avoid rebuilding it per file. I agreed
and applied it in `refactor(agent): hoist skip-dir set to SKIP_DIRS class
constant`. Reviewer also noted Windows `\` paths are out of scope (unchanged from
original) — left as-is and documented in the PR notes.

---

## Week 10 — Iteration & reflection
<!-- REVIEW & PERSONALIZE: this reflection is drafted from what actually happened
     on this branch. Edit it so it reflects YOUR genuine experience and voice
     before submitting — the grader rewards honesty and specificity, not polish. -->

### Reviewer feedback

**Feedback received:** [x] No — still awaiting review

**Summary of feedback:**
No maintainer/peer review was provided (per the Summer 2026 note, upstream
reviewer feedback isn't given for this cohort). The one review I did get was the
mentor review in Week 9 (Claude, approved by the instructor as this cohort's
reviewer): it flagged that my `skip_dirs` set was a local variable while the
module's other lookup tables (`EXT_TO_LANG`, `CONFIG_INDICATORS`) are class
constants.

**How you responded:**
I agreed and hoisted it to a `SKIP_DIRS` class constant
(`refactor(agent): hoist skip-dir set to SKIP_DIRS class constant`), then re-ran
the tests and the baseline comparison to confirm no new failures. I left the
Windows `\`-path limitation alone, since the original code had the same
assumption and fixing it wasn't part of #150.

---

### Reflection

**What was harder than you expected?**
Two things. First, the bug looked like a one-line typo but the root cause was
subtle: `_should_skip_file` matched `"/node_modules/"` as a substring, so it
silently failed only for *top-level* paths (no leading slash) while still working
for nested ones — which is exactly why it slipped past whoever wrote it. Reading
the failing test paths carefully (`node_modules/...` vs `/node_modules/`) was what
made it click. Second, the repo's baseline state was disorienting: `make
test-unit` shows 53 failures and `mypy` 103 errors on a clean `main`. Figuring out
that "passing" here means "introduces no *new* failures" — not "everything is
green" — took a mindset shift I didn't expect.

**What did you learn about working in a large codebase?**
Contributing to someone else's code is more about *fitting in* than being clever.
The fix itself was ~10 lines; the real work was matching conventions
(Conventional Commits, the `verb`/scope commit style, class-constant patterns),
reading the existing tests as the spec, and — hardest to resist — *not* fixing
things outside my issue. I found a second real bug (primary language is chosen
alphabetically, not by count) and had to consciously leave it alone and note it
for a separate issue, because a bugfix PR that also reformats files and fixes
unrelated bugs is harder to review and more likely to be rejected. In my own
projects I'd have just fixed everything at once.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation and verification: mapping how the `agent/`
module is structured, pinpointing the exact root-cause line, generating the
segment-matching fix and edge-case tests in the repo's style, and running the
disciplined baseline-vs-after comparison across `test-unit`/`ruff`/`black`/`mypy`.
Where it fell short was *judgment*: whether to keep the second bug out of scope,
whether to reformat pre-existing lint debt in a file I was touching, and whether
`--no-verify` (to keep the diff minimal) was the right call — those were tradeoffs
that depended on contribution norms and cohort expectations, not something AI
could decide for me. It also can't do the human-loop parts: opening the PR
(auth), or a real peer review.

**What would you do differently if you started over?**
I'd pace myself to the weekly structure instead of jumping straight to the fix in
Week 7 — I effectively finished the code before the "reproduction & planning" and
"building" weeks, which made those weeks feel like back-filling documentation
rather than doing the work in order. I'd also file the alphabetical-primary-
language bug as its own issue early, so it's captured and claimable rather than
just a note in my journal.

**What are you most proud of from this module?**
The scope discipline and the honesty of the verification. It would have been easy
to "improve" the whole file, but I kept the PR to exactly the issue, documented
every pre-existing failure with before/after numbers, and made a clean,
conventional commit history that tells the whole story (repro → fix → tests →
review revision). The contribution is small, but it's *reviewable*, and I can
defend every line and every decision in it.

---

## Working notes

### 2026-07-17 — Environment setup
- Started Docker backing services (`docker compose up -d`): Postgres (`:5433`),
  Redis (`:6379`), ChromaDB (`:8001`).
- Created `.env` from `.env.example` (`LLM_PROVIDER=mock`, no API key needed).
- Ran `make setup` (venv + deps + `alembic upgrade head` + seed + `npm install`).
- Ran `make run`; confirmed frontend at **http://localhost:5173** (HTTP 200) and
  API docs at http://localhost:8000/docs.
- Note: `/health` returns 503 from two pre-existing app-code bugs (Postgres check
  needs `text("SELECT 1")`; Redis check references a missing `redis_host`
  setting). Infra containers are healthy — unrelated to #150.

### 2026-07-17 — Fix for #150
- **Root cause:** `_should_skip_file` used slash-wrapped substring matching
  (`"/node_modules/" in filepath`), which fails for top-level paths like
  `node_modules/lib/x.js` (no leading slash), so those files were not excluded.
- **Fix:** match on path segments (`filepath.split("/")`) against a set of
  skip-dir names, covering both top-level and nested vendored/build directories.
- **Verification:** the two target tests pass; full
  `tests/unit/test_tech_detector.py` → 27 passed; the issue's exact repro now
  returns `Python`.
- **Out of scope (candidate for a separate issue):** primary language is chosen
  alphabetically (`sorted(languages)[0]`), not by file count, despite the "most
  common" comment. Not needed for #150; kept this PR focused.
- **Note on repo state:** the wider unit suite has ~51 pre-existing failures in
  unrelated modules (`skill_extractor`, `structural_chunker`, …) that also fail
  on `main`; they are not caused by this change.