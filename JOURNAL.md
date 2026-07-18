## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/75]

**Issue title:** [Add integration tests for the full safety middleware chain
 #75]

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The `safety/` package has four safety components, each is currently covered only by its own unit test in `tests/unit/`. However, no test runs a request through the complete safety pipeline:

Prompt Defense → Content Filter → Bias Detector → PII Scrubber

The goal of this issue is to verify that the layers behave correctly when combined. To accomplish this, I will add an integration test at `tests/integration/test_safety_middleware.py` with fixtures that exercise the full pipeline end to end. The test should include:

- One passing case that moves through every layer successfully.
- One failing case for each layer that verifies the appropriate guard catches, redacts, or flags the input.

The implementation is considered successful when the integration test confirms that:

- Clean input passes through every layer unchanged.
- Each guard correctly handles its target category while running as part of the full pipeline.

**Branch name:** [test/75-safety-middleware-integration-tests]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Issue Readiness Checklist

### Part 1 — Understanding the Issue

- [x] I can explain what the issue is asking for in my own words.
- [x] I understand which part of the app is affected (`safety/` and `tests/integration/`).
- [x] I understand what "done" looks like (an integration test covering the full safety middleware pipeline).

### Part 2 — Tier Fit

- [x] I understand the issue's tier.
- [x] I chose **Tier 2** because it requires understanding how multiple safety middleware components interact in a single pipeline, but it does not require changing the overall architecture or introducing new system-wide behavior - which is something that is important for me to have expirience on, and I believe I can handle it well.

### Part 3 — Codebase Readiness

- [x] I located the relevant code and files.
- [x] I understand the surrounding code well enough to modify it safely.
- [x] I reviewed the existing tests to understand the testing patterns and structure.

### Part 4 — Scope and Time

- [x] I checked how many others are working on the issue.
- [x] I believe the scope is realistic to complete within the project timeline.
- [x] I confirmed there are no blockers or unresolved dependencies.

### Verdict

- [x] I am ready to claim and work on this issue.