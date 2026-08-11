## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** Tier 1

**Problem summary:**
Prompt templates directly affect review quality. Add snapshot tests that fail if a template's content changes without a version bump, so developers must consciously version templates rather than silently editing them. the part of the codebase it affects is the tests path.

**Branch name:** test/37-add-snapshot-tests-for-prompt-templates

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/hieumile/pathreview/commit/c5f0f10e45b4027b0481eecb513c6d8ffd2e0fa4

**Reproduction summary:**
Altering any prompt template inside `rag/generator/prompt_templates.py` results in a changed MD5 hash, yet `test_template_snapshot_content_hash` continues to pass. This happens because the test only asserts the output is a 32-character string rather than validating it against a reference hash.

**PLAN.md link:** https://github.com/hieumile/pathreview/blob/test/37-add-snapshot-tests-for-prompt-templates/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**
None.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented a robust filesystem-based snapshot system where each prompt template version's expected content is saved as a separate text file under `tests/snapshots/prompt_templates/`.

**Next steps:**
Verify that modifying templates fails the test and reverting passes. Add the option to update snapshots using `UPDATE_SNAPSHOTS=1` environment variable. Prepare the PR for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/765

**Branch:** `test/37-add-snapshot-tests-for-prompt-templates`

**What you built:**
Added snapshot testing for prompt templates. The new `test_template_snapshots` checks active templates in `rag/generator/prompt_templates.py` against reference snapshot files stored under `tests/snapshots/prompt_templates/`. If a template's content is modified without a version bump (and `UPDATE_SNAPSHOTS=1` is not set), the test fails, preventing silent prompt regressions.

**Tests added or updated:**
Modified [test_prompt_templates.py](file:///Users/leminhhieu/github/pathreview/tests/unit/test_prompt_templates.py) to assert the global MD5 content hash matches the reference hash, and added `test_template_snapshots` to check and manage file-based template snapshots.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
*(Note: Pre-existing failures exist in the codebase in other modules/tests, but our changes introduced no new failures).*

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
Still awaiting review from the maintainers.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Configuring the `mypy` strict type checking rules in `pyproject.toml` to ignore test directories without disabling general strict type checking on main source code. The pre-commit hooks strict checking ran on test files but our test setup wasn't fully typed. Standardizing the mypy overrides solved this cleanly.

**What did you learn about working in a large codebase?**
You have to accept and document pre-existing test/lint failures without trying to refactor files outside your scope. Keeping your changes tightly scoped and verifying that your specific features don't introduce any new regressions is key to clean, reviewable PR contributions.

**How did AI tools help — and where did they fall short?**
AI was great at outlining templates and scaffolding files, but fell short in understanding local workspace nuances (such as pre-commit configs vs global check scripts). I had to manually debug the linting environment and design the exact file-based snapshot lookup logic to make the process completely reliable.

**What would you do differently if you started over?**
Set up the pre-commit linting checks early in the first week rather than at the PR stage. This would prevent surprises with tool configs (like mypy and black) later on and allow resolving configuration discrepancies during the initial setup phase.

**What are you most proud of from this module?**
The implementation of filesystem-based snapshots (`.txt` files under `tests/snapshots/`). Having readable text files instead of a single massive JSON dictionary makes visual reviews using `git diff` incredibly clear for reviewers to see prompt text modifications.