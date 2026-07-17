## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/75

**Issue title:** Add integration tests for the full safety middleware chain

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview has unit tests for its individual safety components, but it does not have an integration test that sends a request through the complete safety middleware chain. Without that coverage, interactions among prompt defense, content filtering, bias detection, and PII scrubbing could break without being caught by the existing isolated tests. The issue primarily affects the safety modules and calls for new coverage in `tests/integration/test_safety_middleware.py`. A successful contribution will add reusable fixtures and verify both passing input and rejection or sanitization cases at every layer of the chain.

**Selection notes:**
This issue has a clear deliverable, named components, an expected test location, and concrete pass/fail acceptance criteria. It is limited to integration-test coverage and should not require changing a public API or redesigning production behavior. The estimated 4–7 hour scope is realistic for the Module 3 timeline, and the existing unit tests provide examples for constructing representative fixtures. The main challenge is understanding how the four safety components compose, which is bounded and directly relevant to the requested integration coverage.

**Branch name:** `test/75-safety-middleware-integration-tests`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
