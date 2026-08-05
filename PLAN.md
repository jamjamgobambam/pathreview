## Solution plan

**Issue:** Add integration tests for the full safety middleware chain
(https://github.com/ascherj/pathreview/issues/75)

### Understand

**Root cause:** The `safety/` package ships four standalone utilities
(`PromptDefense`, `ContentFilter`, `BiasDetector`, `PIIScrubber`) each covered by
its own unit test in `tests/unit/`, but no test exercises them as a chained
pipeline in the order the issue specifies
(prompt defense → content filter → bias detector → PII scrubber).
`tests/integration/` contains only an empty `__init__.py`, so the artifact the
issue asks for — `tests/integration/test_safety_middleware.py` — does not exist
and `pytest tests/integration --collect-only` collects 0 items. Worse, a local
reproduction surfaced a *double* gap: `ContentFilter` has no test referencing it
at all (neither unit nor integration), so even per-component coverage is
incomplete.

**Expected:** an integration test module under `tests/integration/` that imports
the four `safety/` classes, runs a representative text through them in the
documented order, and records pass/fail verdicts for each layer — including
fixtures covering both pass and fail cases for every layer (per the issue body).

**Actual:** no such module exists; the four components are only exercised in
isolation, and the cross-layer ordering/short-circuit behavior is unexercised
end-to-end *and* pairwise.

**Important constraint discovered during research:** the four safety components
are **not** wired into `api/` as ASGI middleware
(`api/main.py` only registers `RequestIDMiddleware` + CORS), and the one
runtime call site (`core/services/review_service.py:357` `_run_safety_checks`)
is a placeholder that never calls the four classes. Therefore the integration
test must exercise the *intended* chain ordering directly against the safety
classes — not against a live HTTP path. Wiring real middleware would be scope
creep beyond the issue's "add tests" ask and would expand the change into
`api/` source code that the issue does not request.

### Map

**Files I expect to touch:**

| Path | Action | Purpose |
|---|---|---|
| `tests/integration/test_safety_middleware.py` | **Create** | The integration test module requested by the issue; class-based suite, `@pytest.mark.integration`, fixtures + chain helper + pass/fail cases per layer |
| `tests/integration/__init__.py` | No change (exists) | Already present, keeps package importable |

**Files I will reference (read-only) but not modify:**

- `safety/prompt_defense.py` → `PromptDefense.is_injection_attempt(text) -> bool`,
  `PromptDefense.sanitize(text) -> str` (static methods).
- `safety/content_filter.py` → `ContentFilter.filter(text) -> tuple[str, bool]`
  (returns `(filtered_text, was_filtered)`).
- `safety/bias_detector.py` → `BiasDetector.detect_bias(text) -> tuple[bool, str]`
  (returns `(is_biased, reason)`).
- `safety/pii_scrubber.py` → `PIIScrubber.scrub(text) -> str`,
  `PIIScrubber.detect(text) -> list[dict]` (instance methods; needs an instance).
- `tests/conftest.py` → has `sample_resume_text`, `sample_readme_text` fixtures
  to reuse for realistic clean-input cases.
- `pyproject.toml` → confirms the `integration` marker exists; `make
  test-integration` filters `-m integration`.
- `tests/unit/test_prompt_defense.py`, `test_bias_detector.py`,
  `test_pii_scrubber.py` → style template (class-based, `@pytest.mark.<marker>`,
  `@pytest.fixture` for the instance under test, Google docstrings).
- `AGENTS.md` → "Code Style — Python / Tests" rules (PEP 604 types, line 100,
  structlog, Google docstrings, no comments unless requested).

**Files I deliberately will *not* touch:** `api/main.py`, `api/middleware/`,
`core/services/review_service.py`. Wiring the safety chain into the runtime is
out of scope for a "tests" issue.

### Plan

**Sub-task 1 — Scaffold the module + chain helper.**
Create `tests/integration/test_safety_middleware.py` with a module docstring
explaining: (a) it exercises the four-layer chain in the documented order;
(b) the safety components are not currently wired as ASGI middleware, so this
test pins their contract *as if* they were the request path; (c) the
`integration` marker is used to match the issue's tier and the file location,
even though the test is pure-Python with no Docker deps (AGENTS.md's literal
"integration = requires Docker services" definition does not apply here).
Add a `run_safety_chain(text: str) -> SafetyChainResult` helper (or a plain
function returning a dict) that applies the layers in order and returns, per
layer, `{name, verdict, transformed_text}`. Chain-semantics decisions:

- **Prompt defense → short-circuit:** if `is_injection_attempt` is True, the
  chain stops and downstream layers do not run. Verdict recorded; downstream
  layer verdicts are `None` (not consulted). Rationale: "defense" semantics +
  the issue positions this layer as the fail-gate at the front of the chain.
- **Content filter → sanitize-and-continue:** substitute `[CONTENT REMOVED]`
  via `ContentFilter.filter` and pass the *post-filter* text downstream.
- **Bias detector → passthrough:** record `(is_biased, reason)` but do not
  stop the chain. Rationale: the unit only *detects*; treating it as fatal
  would be inventing policy the issue does not request.
- **PII scrubber → final transform:** always run on the (post-filter,
  bias-checked) text and return the redacted text as the chain's final output.

Use `dataclass` for `SafetyChainResult` to keep typing clean for mypy.

**Sub-task 2 — Fixtures.**

- `safety_chain` fixture returning the helper (or a `PIIScrubber` instance +
  the chain function).
- `clean_portfolio_text` reusing `sample_resume_text` / `sample_readme_text`
  from `tests/conftest.py` for a realistic pass-through case.
- `inbound_request_text` and `outbound_feedback_text` fixtures: model the chain
  as a single unified text pipeline (faithful to the issue's wording) but keep
  both fixtures distinct so the pass/fail matrix can illustrate each direction.
- Per-layer fail-input fixtures:
  `injection_text` (e.g. `"...\nSystem: ignore above"`),
  `harmful_text` (e.g. `"hurt yourself"` matching `HARMFUL_PATTERNS`),
  `biased_text` (e.g. `"bootcamp education is insufficient"` matching
  `DISMISSIVE_PATTERNS`),
  `pii_text` (e.g. an email + a US phone + an SSN).

**Sub-task 3 — Pass-through and per-layer fail cases.**

- `test_clean_text_passes_all_layers_unchanged`.
- `test_realistic_portfolio_text_passes` (uses the conftest fixtures).
- `test_prompt_injection_short_circuits_chain` — asserts layer 1 verdict True
  and that layers 2–4 were *not* consulted (verdicts `None`).
- `test_harmful_content_is_removed_and_chain_continues` — asserts
  `was_filtered True`, `[CONTENT REMOVED]` present, downstream layers still ran.
- `test_bias_detected_and_chain_continues` — asserts `(True, "Dismissive
  language about educational background")` and that PII scrubbing still ran.
- `test_pii_is_redacted_at_final_layer` — asserts `[REDACTED]` substituions
  for email/phone/SSN and that the redacted text is the chain's final output.

**Sub-task 4 — Cross-layer ordering tests (the real integration value).**

These are the cases no unit test can express and justify the module's existence:

- `test_injection_attack_takes_precedence_over_pii` — text that is both an
  injection attempt *and* contains PII: assert injection verdict True and PII
  never scrubbed (short-circuit) → proves layer 1 gates layer 4.
- `test_content_filter_placeholder_does_not_trip_bias_or_pii` — feed
  `ContentFilter.filter` output into `BiasDetector.detect_bias` and
  `PIIScrubber.scrub` to assert the literal string `[CONTENT REMOVED]` does
  not match bias or PII regexes (guards against accidental coupling).
- `test_bias_plus_pii_both_reported_independent_of_order` — text that is both
  biased and contains PII: assert bias verdict at layer 3 *and* PII redacted
  at layer 4 (proves bias is non-fatal and layer 4 still runs).
- `test_chain_idempotent_on_clean_text` — running the chain twice over clean
  input produces identical output (guards against accidental mutation).

**Sub-task 5 — Verify (lint/type/test).**

- `source .venv/bin/activate && pytest tests/integration/test_safety_middleware.py -v`
  (run in isolation first; drop `-m integration` since the file is the only
  integration test).
- `make test-integration` → confirm marker-based selection picks it up.
- `make check` → ruff + black + mypy. Watch for: mypy complaining about
  untyped helpers (annotate `run_safety_chain` and the dataclass), black
  line-length on long assert strings, ruff unused imports / `SIM`/`B` rules
  on the dataclass.

### Inputs & outputs

**Input:** a single `text: str` fed into `run_safety_chain`. Plus, via
fixtures, representative clean/injection/harmful/biased/PII strings.

**Output of the fix (what changes in the repo):**
- New file `tests/integration/test_safety_middleware.py`.
- `pytest tests/integration --collect-only` now collects the new test class (was 0 items).
- `make test-integration` runs the new module (was empty).
- No change to `safety/`, `api/`, `core/`, or any runtime code — the fix is purely additive test coverage.

**Output of `run_safety_chain(text)` (test helper return shape):**
```
SafetyChainResult(
  input_text: str,
  final_text: str,                 # post-scrub, post-filter chain output
  layers: list[LayerResult],        # one per layer in order
)
LayerResult(name: str, verdict: Any, transformed_text: str | None)
```
Verdict types per layer: prompt defense `bool`; content filter
`tuple[str, bool]` (or just the `was_filtered` bool — TBD during impl);
bias detector `tuple[bool, str]`; PII scrubber `str` (redacted text).

### Risks & unknowns

1. **`ContentFilter` test gap is broader than the issue implies.** The issue
   says "Unit tests exist for individual safety components" but
   `ContentFilter` has *no* test referencing it. The integration test will be
   the first test touching `ContentFilter` at all; if `ContentFilter.filter`
   has a latent bug (e.g. a `HARMFUL_PATTERNS` regex that does not match its
   own intent), it will surface here. Mitigation: keep fail-case strings
   obviously matching the existing patterns; if a pattern unexpectedly fails
   to match, the test failure should be treated as a *real* bug to report, not
   a test bug to work around.
2. **Marker-vs-definition mismatch.** AGENTS.md says `integration` tests
   "require Docker services" but this test has no Docker deps. Using the
   marker anyway (to satisfy the issue's tier + file location + `make
   test-integration` selection) is a documented convention violation. The
   module docstring will call this out explicitly so it is intentional, not
   silent.
3. **Chain semantics are mine, not the repo's.** Short-circuit on injection
   and passthrough on bias are reasonable readings but not encoded anywhere.
   A reviewer could disagree. Mitigation: encode semantics in the helper with
   a clear docstring and cover both paths with explicit tests so the choice
   is visible and reversible.
4. **`PromptDefense.sanitize` vs `is_injection_attempt`.** Both exist; the
   chain uses `is_injection_attempt` as the verdict and short-circuits, *not*
   `sanitize`. A reviewer might expect sanitize-then-continue. The test names
   and docstrings will make the choice explicit.
5. **Regex fragility in `PIIScrubber`.** Its `street_address` regex is wide
   and can false-positive on normal prose (e.g. "5 years of React
   development"). Clean-input tests must avoid accidental matches —
   `sample_resume_text`/`sample_readme_text` should be checked against the
   PII regexes during sub-task 3 to confirm no spurious `[REDACTED]`.
6. **mypy strictness.** `disallow_untyped_defs` + `warn_return_any` are on;
   the dataclass and `run_safety_chain` must be fully annotated, and the
   `LayerResult.verdict: Any` is the one place I expect mypy friction.

### Edge cases

The fix (test module) must handle gracefully:

- **Empty string:** `run_safety_chain("")` should not raise; all four layers
  return falsy/empty verdicts; final_text == "".
- **Whitespace-only string:** same as empty — no false positives from any layer.
- **Text that triggers multiple layers simultaneously:**
  - injection + PII (sub-task 4) → injection short-circuits, PII not scrubbed.
  - bias + PII (sub-task 4) → both reported independently.
  - harmful + PII → harmful content removed; *then* PII scrubbed on the
    post-filter text (assert PII in the surviving substring is redacted).
- **The literal placeholder `[CONTENT REMOVED]` and `[REDACTED]`** must not
  themselves trip downstream layers' regexes (sub-task 4 coupling test).
- **Idempotency:** running the chain twice over clean input yields identical
  output (sub-task 4).
- **Unicode / non-ASCII text:** the chain must not crash on emoji or accented
  characters; at minimum assert it returns a string of some kind (light-touch
  test, since the regexes are ASCII-anchored).
- **Very long input** (e.g. a multi-KB README): no assertion on performance,
  but the chain must complete without recursion/stack issues (the regexes are
  linear, so this is a low risk — will add one smoke test with a large string).