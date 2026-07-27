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
