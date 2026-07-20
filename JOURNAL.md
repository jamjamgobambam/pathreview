## Week 7 — Issue selection

**Issue link:** [Issue](https://github.com/ascherj/pathreview/issues/37)

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
There's already a test that looks like a snapshot test for the prompt templates, but it just computes a hash and never checks it against anything fixed, so it passes no matter what changes. That means someone could quietly reword a template and every test would still go green. The fix is to make that test actually compare against a saved expected hash, so it fails unless the version gets bumped on purpose.

**Branch name:** test/37-snapshot-tests-prompt-templates

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger