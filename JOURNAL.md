# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG layer relies on prompt templates whose exact wording drives the quality
of the reviews PathReview generates. Right now nothing guards those templates, so
a developer can edit one and silently change model behavior without anyone
noticing or bumping its version. This issue asks for snapshot tests that capture
each template's current content and fail whenever it changes without a matching
version bump. A successful fix makes template edits a deliberate, reviewable
action — the test forces the author to consciously re-version a template instead
of changing it by accident. The work lives in tests/unit/test_prompt_templates.py
and covers the prompt templates in the rag module.

**Branch name:** test/37-prompt-template-snapshot-tests

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
