## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/75

**Issue title:** Add integration tests for the full safety middleware chain

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, the pathreview safety components (PromptDefense, ContentFilter, BiasDetector, and PIIScrubber) only have individual unit tests, meaning there is no test verifying how they interact together sequentially. The goal is to build an integration test suite with fixtures that simulate full requests flowing through the entire safety middleware chain. A successful implementation will ensure that data correctly passes or fails at the appropriate layers (e.g., prompt injection blocked first, then content filtered, then PII scrubbed), proving the architecture works end-to-end. Based on the "Is this right for me?" checklist: (Part 1) I can explain the problem and expected behavior clearly. (Part 2) This Tier 2 issue is a realistic match for my skills since I have Python testing experience. (Part 3) I found the relevant `safety/` components and tests and understand the context well enough to write a plan. (Part 4) The scope is achievable before Week 9 and there are no blockers.

**Branch name:** feat/75-safety-integration-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/wonsik99/pathreview/commit/8ea5e37

**Reproduction summary:**
I created a failing test skeleton in `tests/integration/test_safety_integration.py` that attempts to run through the safety modules and fails by design, proving the integration test is currently missing.

**PLAN.md link:** https://github.com/wonsik99/pathreview/blob/feat/75-safety-integration-tests/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**
None at this time.
