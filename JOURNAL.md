# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview uses prompt templates to generate its reviews, and even small wording changes can affect the results. Right now, those changes can happen without being noticed or requiring the template version to be updated. This issue adds tests that detect changes to the templates and require a version bump, making edits intentional and easier to review.

The work will be done in tests/unit/test_prompt_templates.py and will cover the prompt templates in the rag module.

**Selection notes — "Is this right for me?" checklist:**
- **Scope is contained:** The work lives in a single file (tests/unit/test_prompt_templates.py) and adds tests rather than changing production code, so the blast radius is small.
- **Matches my skills:** It's a testing task in Python — no need to redesign the RAG pipeline, just capture and assert on existing template content.
- **Effort fits the week:** Estimated at 3–5 hours, which is realistic for a first contribution.
- **Success is clearly defined:** "Done" is unambiguous — a test that fails when a template changes without a version bump. That makes it easy to know when I'm finished.
- **Good first issue:** Labeled tier-1 and "good first issue," which is the recommended starting point for my first contribution to a large codebase.

**Branch name:** test/37-prompt-template-snapshot-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
