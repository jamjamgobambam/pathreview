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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Starscreen2/pathreview/commit/13f67d0180fd4b954f7d20af26de94443c18eda5

**Reproduction summary:** I reproduced the feature gap by confirming that `tests/integration/` contains no safety middleware test and that pytest reports no collected integration tests. The four safety components can be called independently, but no existing code or test sends the same input through the complete documented sequence.

**PLAN.md link:** https://github.com/Starscreen2/pathreview/blob/test/75-safety-middleware-integration-tests/PLAN.md

**Walkthrough video (recommended):** Not recorded (recommended, not graded).

**Blockers or open questions:** The repository has no production safety-chain orchestrator, so the remaining question for Week 9 is whether issue #75 expects only test-local composition in the named integration test or a separate production pipeline. Existing component tests also include unrelated baseline failures, which should not expand this integration-test issue without maintainer direction.
