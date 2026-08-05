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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the full integration test suite in `tests/integration/test_safety_integration.py`. The test file includes a `run_safety_pipeline()` helper that chains all four safety components in the documented order (PromptDefense → ContentFilter → BiasDetector → PIIScrubber) and 14 integration tests organized into five categories: happy-path (4 tests), prompt-injection blocking (4 tests), content filtering (1 test), bias detection (2 tests), and edge cases (3 tests). All 14 tests pass with `make test-integration`.

**Next steps:**
Run `make check` and `make test-unit` to confirm no new failures were introduced. Self-review against CONTRIBUTING.md conventions. Open a PR and request peer feedback.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/323

**Branch:** `feat/75-safety-integration-tests`

**What you built:**
Added `tests/integration/test_safety_integration.py` with a test-local pipeline helper that runs input through all four safety components in sequence. The suite verifies pass-through behavior for clean text, immediate rejection for prompt injection and biased language, content filtering for harmful phrases, PII redaction for emails/phone numbers/SSNs, correct layer ordering for multi-violation payloads, and graceful handling of empty and whitespace-only input.

**Tests added or updated:**
`tests/integration/test_safety_integration.py` — 14 integration tests covering all four safety layers with pass and fail cases for each, plus edge cases. All tests are marked with `@pytest.mark.integration` and collected by `make test-integration`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Pre-existing failures: `make test-unit` reports 53 pre-existing failures in unrelated modules (resume_parser, review_service, skill_extractor, etc.) that existed before this change. `make typecheck` reports a numpy `.pyi` syntax error unrelated to this change. This contribution introduces no new failures.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No

---

### Reflection

**What was harder than you expected?**
Figuring out the API signatures of each safety component. Each class follows a different pattern: `PromptDefense.is_injection_attempt()` is a static method returning a bool, `ContentFilter.filter()` returns a tuple, `BiasDetector.detect_bias()` also returns a tuple, and `PIIScrubber` needs to be instantiated first. There was no central documentation, so I had to read each source file and trace the existing unit tests to confirm the correct signatures.

**What did you learn about working in a large codebase?**
Contributing to someone else's code requires far more reading than writing. Before writing a single test, I spent time navigating the `safety/` directory, cross-referencing `tests/unit/` for patterns, and reviewing `CONTRIBUTING.md` for conventions like `@pytest.mark.integration`. I also learned that pre-existing failures (53 in unrelated modules) are normal, and I had to verify my change introduced zero new ones.

**How did AI tools help, and where did they fall short?**
AI helped with generating boilerplate test structures and suggesting edge cases like whitespace-only input and multi-violation payloads. It fell short when I needed to know the specific behavior of each component, such as what regex patterns `PromptDefense` actually checks. I had to read the source code myself to write test inputs that would reliably trigger each safety layer.

**What would you do differently if you started over?**
I would iterate in smaller batches instead of planning all 14 tests upfront. Writing two or three tests, running them, and then expanding would have helped me catch API misunderstandings faster.

**What are you most proud of from this module?**
The `run_safety_pipeline()` helper and the layer-ordering test. The multi-violation test proves that a payload with both injection and bias gets caught by `PromptDefense` first and never reaches `BiasDetector`. That kind of ordering guarantee is exactly what integration tests are for, and unit tests alone could never verify it.
