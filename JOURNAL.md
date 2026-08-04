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
[PLAN.md](./PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All five PLAN.md sub-tasks are complete. I created
`tests/integration/test_safety_middleware.py` with a `run_safety_chain` helper
(returns a `SafetyChainResult` dataclass of per-layer `LayerResult`s) encoding
the four-layer ordering (prompt defense → content filter → bias detector → PII
scrubber) and the short-circuit / passthrough semantics. The 16-test suite
covers per-layer pass/fail cases (including reuse of the shared
`sample_resume_text` / `sample_readme_text` fixtures), cross-layer ordering
the unit tests can't express (injection short-circuit over PII, content-filter
placeholder not tripping downstream layers, bias + PII both reported
independently, chain idempotency), and edge cases (empty / whitespace-only /
unicode / large input). All 16 pass; the file is clean under `ruff`, `black`,
and the pre-commit `mypy` hook (fully annotated — `SafetyChain` callable alias,
`-> None` on every test method, `str | None` narrowing asserts). Baseline
`make check` / `make test-unit` numbers recorded before and after the change
and are identical — no new failures introduced.

**Next steps:**
Final self-review pass — re-read `docs/CONTRIBUTING.md` to confirm branch name
(`feat/75-safety-middleware-integration-tests`) and commit message follow
Conventions — then open the PR with the `PR.md` body, request a draft review,
and fold in any feedback before the Sunday deadline.

**Blockers:**
None. (One noted out-of-scope pre-existing bug: `PIIScrubber.phone_us` does
not redact the parenthesized `(555) 123-4567` format — the `pii_text` fixture
uses the hyphenated form so the integration test stays focused on chain
behavior; fixing that regex would be a separate `fix(safety):` issue.)

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/759

**Branch:** feat/75-safety-middleware-integration-tests

**What you built:**
Added the first integration test for the `safety/` package
(`tests/integration/test_safety_middleware.py`) — a 16-test suite that runs a
representative text through the four safety layers in the order required by
the issue via a `run_safety_chain` helper, asserting the per-layer verdicts
plus the cross-layer ordering (injection short-circuits downstream PII,
content-filter placeholder doesn't trip bias/PII, bias is non-fatal so PII
still scrubs, chain is idempotent). No runtime code touched — purely
additive test coverage that makes `make test-integration` collect 16 items
(was 0).

**Tests added or updated:**
- `tests/integration/test_safety_middleware.py` (new, 16 tests):
  `run_safety_chain` chain helper + `SafetyChainResult` / `LayerResult`
  dataclasses; per-layer pass/fail cases for prompt defense, content filter,
  bias detector, and PII scrubber (incl. reuse of `sample_resume_text` /
  `sample_readme_text` from `tests/conftest.py`); cross-layer ordering tests
  (injection-over-PII, placeholder coupling, bias + PII, idempotency); and
  edge-case smoke tests (empty, whitespace, unicode, large input,
  harmful + PII).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

