
## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The application’s prompt templates directly influence the quality and consistency of generated reviews, but there are currently no snapshot tests protecting their content. This means a developer could accidentally modify a prompt template without updating its version, causing unexpected behavior that may be difficult to notice during review. The issue affects the prompt-template unit tests in `tests/unit/test_prompt_templates.py`. A successful fix will add snapshot tests that fail whenever a prompt changes without an intentional version bump, ensuring prompt updates are reviewed and versioned deliberately.

**Branch name:** `test/issue-37-prompt-template-snapshots`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
