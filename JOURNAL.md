## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/75

**Issue title:** Add integration tests for the full safety middleware chain

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, the pathreview safety components (PromptDefense, ContentFilter, BiasDetector, and PIIScrubber) only have individual unit tests, meaning there is no test verifying how they interact together sequentially. The goal is to build an integration test suite with fixtures that simulate full requests flowing through the entire safety middleware chain. A successful implementation will ensure that data correctly passes or fails at the appropriate layers (e.g., prompt injection blocked first, then content filtered, then PII scrubbed), proving the architecture works end-to-end.

**Branch name:** feat/75-safety-integration-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
