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

## Week 9 — Implementation & pull request

### Check-in 1 — Mid-week

**Current progress:** I implemented a test-local safety stack that runs input through prompt defense, content filtering, bias detection, and PII scrubbing in sequence. I added reusable fixtures and seven integration tests for clean input, prompt injection, harmful content, biased content, PII, combined transformations, and empty input.

**Next steps:** Run the repository checks, document any baseline failures, self-review the changes, and prepare the pull request for review.

**Blockers or open questions:** The repository still does not expose a production orchestrator for all four middleware components, so this contribution composes the existing public component interfaces inside the integration test. Repository-wide checks also contain failures unrelated to this test-only change.

### Check-in 2 — End-week

**Pull request:** https://github.com/ascherj/pathreview/pull/320

**Branch:** `test/75-safety-middleware-integration-tests`

**What I built:** I added `tests/integration/test_safety_middleware.py`, which exercises the complete safety sequence using the existing component interfaces without changing application behavior. The suite verifies both safe pass-through behavior and the expected detection, blocking, or redaction behavior at each layer.

**Tests added:** Seven integration tests cover clean input, injection detection and sanitization, harmful-content filtering, bias detection, PII redaction, combined transformations, and empty input. `make test-integration` passes with 7 tests.

**Self-review confirmation:** [x] The changed file passes formatting, linting, type checking, and pre-commit checks; repository-wide baseline failures are documented in the pull request. [x] The change introduces no new unit-test failures; the existing `make test-unit` result is documented in the pull request.

**Feedback source:** None yet. The pull request requests reviewer feedback on the test-local integration boundary.
