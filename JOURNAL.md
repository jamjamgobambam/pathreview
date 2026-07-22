# Module 3 Journal

## Week 7 — Issue Selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** ☑ Tier 1 ☐ Tier 2 ☐ Tier 3

### Problem summary

The issue is in the README scoring tests. One of the test fixtures contains only about 51 words, but the test expects it to be classified as a comprehensive README with more than 100 words. Because of this mismatch, the test fails even though the scoring logic itself appears to be working correctly. The fix will involve updating either the test fixture or the expected assertion so the test reflects the intended behavior.

### Why I chose this issue

- The issue is well scoped and has a clear expected outcome.
- It appears to involve only the test suite, making it a good first contribution.
- It is a Tier 1 issue that matches my current experience with the project.
- Working on this issue will help me become familiar with the project's testing framework and contribution workflow.

**Branch name:** `test/156-readme-scorer-fixture`

**Setup confirmation:** ☐ App runs locally at `http://localhost:5173` *(to be updated after setup is verified.)*

**Cohort ledger:** ☑ Added issue to the cohort ledger