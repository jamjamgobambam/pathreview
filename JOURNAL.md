## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/75]

**Issue title:** [Add integration tests for the full safety middleware chain
 #75]

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

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

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue Readiness Checklist**

1. Understanding the Issue

- [x] I can explain what the issue is asking for in my own words.
- [x] I understand which part of the app is affected (`safety/` and `tests/integration/`).
- [x] I understand what "done" looks like (an integration test covering the full safety middleware pipeline).

2. Tier Fit

- [x] I understand the issue's tier.
- [x] I chose **Tier 2** because it requires understanding how multiple safety middleware components interact in a single pipeline, but it does not require changing the overall architecture or introducing new system-wide behavior - which is something that is important for me to have expirience on, and I believe I can handle it well.

3. Codebase Readiness

- [x] I located the relevant code and files.
- [x] I understand the surrounding code well enough to modify it safely.
- [x] I reviewed the existing tests to understand the testing patterns and structure.

4. Scope and Time

- [x] I checked how many others are working on the issue.
- [x] I believe the scope is realistic to complete within the project timeline.
- [x] I confirmed there are no blockers or unresolved dependencies.

I am ready to claim and work on this issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [18d01b1](https://github.com/noamreiner17/pathreview/commit/18d01b10fa923026eb96a1b8810f7233fdcad1e7)

**Reproduction summary:**
Because #75 is a missing-coverage issue, I reproduced the gap rather than a runtime crash: `tests/integration/` held only an empty `__init__.py`, and the four guards are imported only by their own unit tests in `tests/unit/` — never together. I added `tests/integration/test_safety_middleware.py` with a red marker test. `pytest tests/integration/test_safety_middleware.py` fails with "integration coverage ... not yet implemented (#75)", confirming the pipeline (Prompt Defense → Content Filter → Bias Detector → PII Scrubber) has no
end-to-end test and pinpointing where it belongs.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Blockers or open questions:**
The four guards have inconsistent interfaces (static vs. instance methods, different return shapes) and `PromptDefense.sanitize` strips characters that later guards may rely on, so I still need to confirm a fixture ordering that isolates each layer without one guard masking another.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Using plan.md as a guide for the AI. This week I implemented the full integration test in `tests/integration/test_safety_middleware.py`, replacing the Week 8 reproduction marker. Wrote a `run_safety_pipeline` helper that chains the four guards in order (prompt defense → content filter → bias detector → PII scrubber) and returns which guards fired. Completed PLAN.md sub-tasks 1–3: the pipeline helper, the clean pass case, and a failing fixture per layer.

**Next steps:**
Reciving PR feedback, and fixing it if nessecery. 

**Blockers:**
None. 

---
### Check-in 2 - Will complete after PR

**PR link:** [#457](https://github.com/ascherj/pathreview/pull/457)

**Branch:** `test/75-safety-middleware-integration-tests`

**What you built:**
An end-to-end integration test for the safety middleware chain. A `run_safety_pipeline` helper runs a request through all four guards in the documented order (Prompt Defense → Content Filter → Bias Detector → PII Scrubber) and records which fired; the suite asserts clean input passes untouched and that each guard catches, redacts, or flags its own category — individually and when multiple guards fire on one request. No production code changed — the deliverable is test coverage.

**Tests added or updated:**
`tests/integration/test_safety_middleware.py` (new) — 11 tests: one clean pass case, one fail case per layer (injection, harmful content, bias, PII), a prompt-defense sanitization case, a combined injection+PII case, and edge cases for empty/whitespace input and a PII near-miss. This is also the first test to exercise `ContentFilter` at all.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes  [x] make test-integration passes (all 11 green via `pytest tests/integration -v -m integration`; the `integration` marker is registered in `pyproject.toml` and the file collects without Docker)

*Note on pre-existing failures:* Before my changes, `make test-unit` already had 53 failing tests and `make check` reported 182 lint errors, all in files unrelated to #75. My change only adds `tests/integration/test_safety_middleware.py`, which passes ruff/black/mypy and all 11 of its tests; it introduces no new failures.

**Draft PR feedback received from:** peer reviewer (cohort).

**Review response:** My reviewer is Shawn Blackman. The reviewer confirmed the tests exercise the real guards end to end and that the `fired()` set correctly proves guard isolation. They raised four points: (1) `run_safety_pipeline` hand-assembles the guards rather than importing production wiring, so composition/ordering isn't verified against production; (2) the sanitize-delimiter test asserts the end state rather than isolating `sanitize`; (3) confirm the tests actually run under `make test-integration` and aren't silently deselected; and (4) general praise. I looked over the suggestions and concluded no code changes were needed: point 1 is out of scope for #75 (the issue explicitly excludes changes to `review_service._run_safety_checks`), so I instead documented in the PR that production ordering remains unverified; point 2 the reviewer themself marked "fine as is"; and point 3 I verified directly — all 11 tests pass under `pytest tests/integration -v -m integration` with the `integration` marker registered in `pyproject.toml` and no Docker required, so the checklist claim holds.