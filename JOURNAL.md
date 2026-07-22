## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/75

**Issue title:** Add integration tests for the full safety middleware chain

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Unit tests exist for the individual `safety/` components (prompt defense, content
filter, bias detector, PII scrubber), but no test runs a request through the
full safety stack in the order listed in the issue
(prompt defense → content filter → bias detector → PII scrubber). The
`tests/integration/` directory currently has only an `__init__.py`, so the
`test_safety_middleware.py` module requested by the issue does not exist yet.
A successful fix adds that integration test module with fixtures covering pass
and fail cases for each layer. (Estimated effort per the issue: 4–7 hours.)

**Branch name:** feat/75-safety-middleware-integration-tests

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**Selection reason** I have software development experience and have contributed to open source projects in the past, so I think this issue has the right difficulty for me.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 


**Reproduction summary:**
Confirmed locally (Python 3.11.13, `LLM_PROVIDER=mock`, branch
`feat/75-safety-middleware-integration-tests`) that the issue is a missing-test
gap: `tests/integration/` holds only an empty `__init__.py` (no
`tests/integration/test_safety_middleware.py`), `python -m pytest
tests/integration --collect-only` collects 0 items, and no test anywhere chains
two or more safety components — `ContentFilter` has no test referencing it at
all. Per-component coverage is unit-only (`test_prompt_defense.py`,
`test_bias_detector.py`, `test_pii_scrubber.py`), so the four-layer pipeline
(prompt defense → content filter → bias detector → PII scrubber) is unexercised
end-to-end and even pairwise.

**PLAN.md link:**

**Walkthrough video (recommended):**

**Blockers or open questions:**
