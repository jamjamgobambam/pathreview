# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

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

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> "Passes" here means my change introduces **no new failures** in a repo with documented
> pre-existing failures. Baseline before my change: `53 failed, 375 passed` (`make test-unit`)
> and 182 pre-existing `ruff` errors (`make check`). After my change: `53 failed, 376 passed`
> (my net +1 test, my file fully green) and no new `ruff`/`black`/`mypy` errors on the lines I
> added. The pre-existing failures live entirely in files I did not touch (e.g.
> `test_resume_parser.py`, `test_review_service.py`, `test_skill_extractor.py`) plus
> pre-existing lint/type debt in the untouched portions of `test_prompt_templates.py`.

**Draft PR feedback received from:** <!-- TODO: name or Slack handle, or "none" -->
