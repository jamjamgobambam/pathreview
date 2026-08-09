# Module 3 Journal

> Running record of my progress on **PathReview** throughout Module 3.
> A new section is added each week.
> Fork: https://github.com/arunkasala-open/pathreview

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/28

**Issue title:** Generator produces duplicate feedback sections when a user has multiple projects in the same tech stack

**Tier:** [ ] Tier 1 [ ] Tier 2 [x] Tier 3

**Problem summary:**
The review generator treats each of a user's projects independently, so when
someone has several projects built with the same stack (for example three
Python projects), it produces almost the same skills feedback for each one and
the overall review ends up repetitive and padded. The current
`_consolidate_feedback` step in `rag/generator/review_generator.py` only removes
duplicates by section name, not by the actual content of the feedback, so
repeated observations across similar projects still slip through. A successful
fix would detect when the same observation applies to multiple same-stack
projects and consolidate those into a single, cross-project comment. The result
should be a review that reads as a cohesive assessment of the portfolio rather
than a per-project checklist, affecting the RAG generation layer
(`rag/generator/review_generator.py` and `rag/generator/output_parser.py`).

**Branch name:** fix/28-duplicate-feedback-sections-when-multiple-projects

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes — "Is this right for me?"

- **Do I understand the problem?** [x] Yes. I can point to the exact cause: the
  generator scores each project in isolation and `_consolidate_feedback` in
  `rag/generator/review_generator.py` only dedupes by section name, not by
  content, so same-stack projects produce repeated observations.
- **Is the scope appropriate (not too big, not trivial)?** [x] Yes. It's a
  Tier 3 issue estimated at ~7–10 hours in the issues manifest. It's contained
  to the RAG generation layer (two files: `review_generator.py` and
  `output_parser.py`) rather than spanning ingestion, API, and frontend, so the
  blast radius is bounded and reviewable.
- **Is it in a part of the codebase I can navigate?** [x] Yes. I've already read
  the generator and parser modules while setting up, and the logic is
  self-contained Python with clear entry points (`generate_full_review`,
  `_consolidate_feedback`).
- **Can I test/verify the fix?** [x] Yes. The behavior is deterministic given a
  fixed set of chunks, so I can write unit tests under `tests/unit/` that feed a
  profile with multiple same-stack projects and assert that overlapping
  observations are consolidated into a single cross-project comment.
- **Does the effort fit my available time this module?** [x] Yes. A ~7–10 hour
  Tier 3 item is a realistic single-issue commitment for Module 3.
- **Is it unclaimed / not already in progress?** [x] Yes. Confirmed against the
  cohort ledger before claiming, and recorded my name there.

**Scope reasoning:** I'm deliberately limiting this fix to consolidation *within
the generator output* — detecting and merging duplicate cross-project
observations. I am **not** changing the retrieval layer, the prompt templates,
or the review data model, since those are out of scope for this issue and would
expand the blast radius. If deduplication turns out to need richer metadata
(e.g. per-project tech-stack tags), I'll note that as a follow-up rather than
widen this issue.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/arunkasala-open/pathreview/commit/ed4d09e42beafd07220784bcafe3eba542bbe341

**Reproduction summary:**
I added a unit test (`tests/unit/test_issue_28_duplicate_feedback.py`) that
feeds the parse → consolidate path an LLM payload for three same-stack Python
projects with identical "Python skills" content. After
`ReviewGenerator._consolidate_feedback` runs, all three duplicate sections
survive (expected 1), confirming the bug: consolidation dedupes by
`section_name` only and never compares content. The failing assertion is marked
`xfail(strict=True)` so it documents the reproduction now and will flip to a
signal to remove the marker once the fix lands.

**PLAN.md link:** https://github.com/arunkasala-open/pathreview/blob/fix/28-duplicate-feedback-sections-when-multiple-projects/PLAN.md

**Walkthrough video (recommended):** _(not recorded yet)_

**Blockers or open questions:**
- Choosing the content-similarity threshold for merging "nearly identical"
  feedback without collapsing genuinely distinct observations — I'll tune this
  with tests.
- Whether to add an optional `projects` field to `FeedbackSection` (cleaner) or
  encode the affected projects in the content string (less invasive); depends on
  how `_add_citations` and the API review schema consume it.
- Pre-existing `mypy` error in `output_parser.py` (dead `sections = []`, present
  on `main`) blocks the pre-commit hook / CI on any commit touching these files;
  I'll fix it as part of the solution PR.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix. Reworked `ReviewGenerator._consolidate_feedback`
(PLAN sub-tasks 1–3) to group feedback by content similarity and merge each
group into one cross-project comment, added the `_normalize_content` and
`_merge_sections` helpers, and added an optional `FeedbackSection.projects`
field to record which projects a merged section covers. Removed the dead
`sections = []` that tripped ruff/mypy (sub-task 5).

**Next steps:**
Finish expanding the tests (PLAN sub-task 4) with the edge cases, run the full
self-review (`make check` / `make test-unit`) against the recorded baseline to
confirm no new failures, then open the PR.

**Blockers:**
Deciding the similarity threshold — settled on a conservative `0.9` guarded by a
"distinct feedback preserved" test.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/593

**Branch:** `fix/28-duplicate-feedback-sections-when-multiple-projects`

**What you built:**
`_consolidate_feedback` now groups feedback sections by normalized-content
similarity (`difflib`, threshold 0.9) and merges each group into a single
section that lists the projects it applies to and unions their suggestions —
replacing the old dedup-by-`section_name`, which left one repeated observation
per same-stack project.

**Tests added or updated:**
`tests/unit/test_issue_28_duplicate_feedback.py` — promoted last week's `xfail`
reproduction to a passing test and added 8 more: exact and near-identical
merges, distinct feedback preserved, suggestion union/dedup, project recording,
empty and single-section inputs, and the same-`section_name`/different-content
case the old code silently dropped. 9 tests, all passing.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> **Pre-existing failures (per course guidance).** `main` already has 53 failing
> unit tests, 182 `ruff` errors, and a `mypy` numpy-stub error, all unrelated to
> issue #28. I recorded the baseline before starting and confirmed my changes
> introduce **no new failures** (the set of failing unit tests is identical
> before/after; ruff dropped 182→178, black 52→50 as my touched files are now
> clean). "Passes" above is used in that sense — my changes do not make anything
> worse. Details are documented in the PR description.

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review has come in yet. PR [#593](https://github.com/ascherj/pathreview/pull/593)
is open and marked ready for review, but its CI checks are in
`action_required` state — GitHub holds workflow runs on pull requests from a
first-time contributor's fork until an upstream maintainer approves them, so the
checks have not executed and no maintainer or peer has reviewed the change.

**How you responded:**
Nothing to change yet. I re-verified the diff is clean (three files, ruff- and
black-clean, nine passing tests) so the PR is ready the moment a reviewer or CI
run picks it up. If feedback arrives I'll address it on the branch and the PR
will update automatically.

---

### Reflection

**What was harder than you expected?**
The environment setup was harder than the actual bug fix. `make setup` quietly
built the virtualenv with Python 3.8 (because `python` wasn't on PATH and it
fell back to `python3`), which pulled an old setuptools that rejected the
`license = "MIT"` field in `pyproject.toml` — an error whose message pointed
nowhere near the real cause. On top of that the pinned ChromaDB image
crash-looped on NumPy 2.0. Neither had anything to do with issue #28, and
untangling "is this me or the repo?" for each failure took real discipline.

**What did you learn about working in a large codebase?**
That reading comes before writing, and assumptions are expensive. The clearest
example: there are two different `FeedbackSection` types — a `@dataclass` in
`rag/generator/output_parser.py` that the generator uses, and a separate pydantic
model in `api/schemas/review.py` that the service layer uses. If I'd assumed they
were the same, adding a field would have looked far riskier than it was. I also
learned that in someone else's production code you inherit their debt: the repo
had 53 failing unit tests and 182 lint errors before I touched anything, so
"passing" had to mean "I introduced no *new* failures," which I could only prove
by recording a baseline first and diffing against it. In my own projects I'd
just fix everything; here, staying in scope was the professional move.

**How did AI tools help — and where did they fall short?**
AI was fastest at navigation and boilerplate: locating the buggy
`_consolidate_feedback`, tracing who constructed `FeedbackSection`, drafting the
`difflib`-based similarity approach, and generating the edge-case tests and the
PR body. Where it fell short was judgment and external reality. It couldn't tell
me the right similarity threshold — I had to reason about false merges and guard
it with a "distinct feedback preserved" test. It couldn't verify "pre-existing
vs. new failure" for me; that only came from actually running the baseline. And
it couldn't cross the real-world gates at all: creating the PR, approving fork
CI, and getting a human review are things no tool could do on my behalf.

**What would you do differently if you started over?**
I'd weigh *runnability* when selecting the issue. Issue #28 lives in the RAG
generator, but `_run_rag_retrieval_generation` in the service layer is still a
placeholder, so there's no live end-to-end path — I could prove the fix with
unit tests but never demo it in the running app. Next time I'd favor an issue I
can trigger through the actual UI. I'd also open the draft PR earlier in the
cycle to leave room for peer review, and capture the CI baseline in Week 8 during
reproduction rather than at implementation time.

**What are you most proud of from this module?**
The rigor around "do no harm," not the fix itself. I committed the reproduction
first as a strict-`xfail` test so it documented the bug and would automatically
flip to a failure-signal once fixed, recorded a full baseline of the repo's
pre-existing failures, and proved with a sorted diff of failing test IDs that my
change added zero new failures while actually reducing lint errors. Turning a
messy, half-broken codebase into a confident, well-scoped, and *verifiable*
contribution is the part I'll carry forward.

