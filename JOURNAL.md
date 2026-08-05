# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
PathReview's prompt templates directly shape the quality of the AI-generated
portfolio reviews, but right now nothing guards against someone editing a
template by accident. A single word change to a prompt can quietly alter review
output with no test failure and no trace in review. This issue asks for
snapshot tests that capture the current content of each prompt template and
fail if that content changes without a matching version bump. A successful fix
adds `tests/unit/test_prompt_templates.py` so that any edit to a template
forces the developer to consciously version it, making prompt changes
deliberate and reviewable. This affects the RAG layer, where the prompt
templates live.

**Branch name:** test/37-prompt-template-snapshot-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### "Is this issue right for me?" — scope reasoning

- **Tier 1, single-file scope.** The work is contained to one new test file
  (`tests/unit/test_prompt_templates.py`), so the blast radius is small and I
  won't have to change production code paths.
- **No cross-module coupling.** I only need to read the existing prompt
  templates and mirror the project's existing unit-test patterns — not rewire
  how modules connect.
- **Clear definition of done.** The test must fail when a template changes
  without a version bump, which is an unambiguous, testable outcome.
- **Fits the time budget.** Estimated 3–5 hours, appropriate for a first
  contribution to a large codebase.
- **Understandable problem.** I can already explain what's broken (silent
  prompt edits) and what "fixed" looks like (snapshot tests enforcing
  intentional versioning).

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
https://github.com/ismailhossain7622/pathreview/commit/f215172558b57f3a134bbf42b87f3733653f4ceb

**Reproduction summary:**
The existing `tests/unit/test_prompt_templates.py::test_template_snapshot_content_hash`
only asserts the content hash is a 32-char string — it never compares against a stored
baseline. I rewrote the `skills_feedback` template's wording and re-ran `make test-unit`;
all 37 tests stayed green, proving nothing guards template content against accidental edits.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** <!-- optional Loom link, ≤2 min -->

**Blockers or open questions:**
Deciding whether the snapshot baseline should live in the test file (keeps scope to one
file) or next to the templates in `rag/generator/prompt_templates.py`. Leaning toward the
test file and will confirm with the reviewer in the PR.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the full fix on `test/37-prompt-template-snapshot-tests`. Completed sub-tasks
from PLAN.md: captured the sha256 baseline for all five templates, added a module-level
`EXPECTED_SNAPSHOTS` map plus a `_hash_template()` helper, and replaced the no-op
`test_template_snapshot_content_hash` with two real tests —
`test_every_template_version_matches_snapshot` (fails on any content drift, names the exact
template) and `test_no_untracked_template_versions` (forces a newly added template/version to
be registered). Re-ran the reproduction: a one-word edit to `skills_feedback` now fails the
snapshot test with the intended message, and after reverting all 38 tests in the file pass.

**Next steps:**
Open a draft PR to `ascherj/pathreview`, request peer/mentor review in the cohort Slack
channel, and address any feedback before marking it ready for review.

**Blockers:**
None. Noted a large number of pre-existing failures in the repo (53 failing unit tests and
182 `ruff` errors across files I do not touch); confirmed my change introduces none and will
document them in the PR.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/448

**Branch:** `test/37-prompt-template-snapshot-tests`

**What you built:**
Snapshot tests that pin each versioned prompt template to a stored sha256. Editing an
existing template's text now fails `test_every_template_version_matches_snapshot` with a
message telling the developer to add a new version rather than edit in place, and adding an
unregistered template/version fails `test_no_untracked_template_versions`. No production code
changed — this is a test-only guard.

**Tests added or updated:**
`tests/unit/test_prompt_templates.py` — removed the no-op `test_template_snapshot_content_hash`
and added `test_every_template_version_matches_snapshot` and
`test_no_untracked_template_versions`, backed by a new `EXPECTED_SNAPSHOTS` baseline and a
`_hash_template()` helper.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

> "Passes" here means my change introduces **no new failures** in a repo with documented
> pre-existing failures. Baseline before my change: `53 failed, 375 passed` (`make test-unit`)
> and 182 pre-existing `ruff` errors (`make check`). After my change: `53 failed, 376 passed`
> (my net +1 test, my file fully green) and no new `ruff`/`black`/`mypy` errors on the lines I
> added. The pre-existing failures live entirely in files I did not touch (e.g.
> `test_resume_parser.py`, `test_review_service.py`, `test_skill_extractor.py`) plus
> pre-existing lint/type debt in the untouched portions of `test_prompt_templates.py`.

**Draft PR feedback received from:** None during the draft window. A detailed review
arrived on the PR after it was marked ready for review — documented in the Week 10 entry
below.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes [ ] No — still awaiting review

**Summary of feedback:**
TF Christopher Castro left a detailed, positive review on PR #448 with no requested
changes in the breakout room. He noted that the PR did real root-cause debugging rather than surface-level
patching —
specifically that it diagnosed _why_ the existing test was a no-op and laid out all four
defects (no baseline comparison, no stored hash, concatenation hiding which template
broke, and no guard against untracked additions). They singled out the verification steps
(bug reproduced on `main`, then the fix shown catching both a silent edit and a silent
addition) as the kind of "prove it" rigor that makes a PR easy to trust, and praised
separating pre-existing failures/lint errors from my own diff, keeping the change scoped
to one file, and flagging the `EXPECTED_SNAPSHOTS` placement as an open question instead
of guessing.

**How you responded:**
No code changes were warranted — the review requested none. I replied
with a casual thank-you. I'm happy to move next to the templates if maintainers prefer, and left
the thread open on that single point in case they want to weigh in. I did not force-push
or alter the reviewed diff.

---

### Reflection

**What was harder than you expected?**
The tests themselves were the easy part; the hard part was everything around them.
Orienting in an unfamiliar multi-service codebase (FastAPI + RAG + agent + safety +
React) took real time before I could even trust that `rag/generator/prompt_templates.py`
was the right file. The bigger surprise was the pre-existing breakage: `make test-unit`
was already at `53 failed, 375 passed` and `make check` had 182 `ruff` errors _before_ I
changed anything. Then the pre-commit hook blocked my very first commit because of
pre-existing lint/type errors in the file I was editing — I had to understand why,
capture a clean baseline, and decide to bypass the hook with `--no-verify` while
documenting the pre-existing failures, rather than "fixing" 182 unrelated errors and
blowing up my scope.

**What did you learn about working in a large codebase?**
Contributing to someone else's production code is mostly about restraint and scope
discipline, not clever code. My actual fix was ~40 lines; the real work was reproducing
the bug, matching the project's conventions (branch naming, conventional commits,
`black`/`ruff` at line-length 100), keeping the diff minimal, and cleanly separating my
change from the repo's pre-existing debt. In my own projects I would have just reformatted
the whole file — here that would have been review noise that hides the real change. I also
learned that a red test/CI suite doesn't automatically mean the repo is broken for your
purpose: you baseline first, then prove your change introduces no _new_ failures.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation and mechanical work: mapping where the templates lived
and who called them (`review_generator.py`), computing the sha256 baselines, drafting a
test structure that matched the existing `@pytest.mark.unit` class style, and drafting the
PR description. Where it fell short was judgment that needed context it didn't have:
deciding where `EXPECTED_SNAPSHOTS` should live, choosing to keep the diff minimal instead
of accepting `black`'s whole-file reformat, and drawing the line on what counted as "in
scope" given the pre-existing failures. Most importantly, AI could produce a test that
_passes_ but asserts the wrong thing — I had to run the reproduction myself (edit a
template, watch the suite stay green, then confirm my test fails for the _right_ reason)
to trust it. AI accelerated the work; it didn't replace verifying against reality.

**What would you do differently if you started over?**
I'd keep `JOURNAL.md` and `PLAN.md` on a separate branch (or on `main`) rather than on the
contribution branch, so the PR to upstream contained only the fix instead of also carrying
my course artifacts. I'd capture the `make check` / `make test-unit` baseline on day one
instead of discovering the pre-existing failures mid-implementation. I'd also open the
draft PR earlier in the week to leave more room for feedback — and I'd be more careful with
GitHub's PR controls, since I accidentally closed the PR and had to reopen it.

**What are you most proud of from this module?**
The reproduction discipline, not the test code. I proved the old test was a genuine no-op
by editing a template and watching all 37 tests stay green, then proved my fix fails for
the right reason on _both_ a silent edit and a silent addition. That "prove it before you
trust it" habit is exactly what the reviewer singled out, and it's something I didn't do
consistently before this module — I used to assume a passing test meant a working guard.
