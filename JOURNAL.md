## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes.

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Prompt templates drive the wording and structure of generated review output, so even small edits can change review quality or formatting. The current test coverage checks that templates exist and contain placeholders, but it does not lock the exact prompt text for each version, so template bodies can drift silently. Adding snapshot coverage in `tests/unit/test_prompt_templates.py` will make any content change fail unless developers intentionally add a new version and update the snapshot. That keeps prompt evolution explicit and prevents accidental regressions in review behavior.

**Branch name:** test/37-prompt-template-snapshots

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger