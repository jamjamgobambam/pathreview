# Week 8 Solution Plan

## Solution plan

**Issue:** [No property-based tests for the PII scrubber](https://github.com/ascherj/pathreview/issues/111)

### Understand

The safety-layer scrubber is implemented in `safety/pii_scrubber.py`, while its current unit coverage is in `tests/unit/test_pii_scrubber.py`. The current suite uses hand-written examples for email, phone, SSN, and address formats, so it does not explore randomized variations that could expose regex gaps. The expected solution is a reproducible Hypothesis-based test layer that checks the scrubber's invariants across supported PII formats; production scrubber behavior is not changed as part of this Week 8 planning work.

### Map

- `safety/pii_scrubber.py`: `PIIScrubber.PII_PATTERNS`, `scrub()`, and `detect()` define the behavior under test.
- `tests/unit/test_pii_scrubber.py`: existing fixed-example tests and the future home for property-based tests.
- `pyproject.toml`: declares `hypothesis>=6.92.0` in the development dependencies.
- `JOURNAL.md`: Week 8 reproduction evidence and the link to this plan.

### Plan

1. Define deterministic Hypothesis strategies for valid emails, US and international phone formats, SSNs, and supported street addresses.
2. Add properties that verify generated PII is removed or masked by `scrub()` and that `detect()` reports the generated value with a valid span.
3. Add mixed-input and invariant properties for preserving unrelated text, handling multiple PII values, and keeping scrubbing idempotent.
4. Run the existing unit suite together with the new property tests, record any baseline failures separately, and use bounded Hypothesis examples so failures are reproducible.
5. Review generated cases for regex overlap and false positives before proposing the implementation for the later module week.

### Inputs & outputs

- **Inputs:** generated PII values, fixed non-PII text, and mixed messages containing both.
- **Outputs:** scrubbed text with generated PII absent or replaced by `[REDACTED]`; detection records whose values and start/end spans match the original input.
- **Test artifacts:** focused property tests in `tests/unit/test_pii_scrubber.py`, reproducible Hypothesis failure examples when a property fails, and a passing focused test command after the later implementation.

### Risks & unknowns

- The broad street-address regex can overlap with ordinary prose, so address strategies must avoid accidentally testing unrelated matches until the intended behavior is agreed.
- Phone formats may overlap between `phone_us` and `phone_intl`; properties should assert the privacy invariant rather than require one exact detector label unless the implementation contract says otherwise.
- The current baseline run has five failures in the existing fixed-example suite, including phone and address behavior. Those failures need separate triage and are not silently attributed to Issue #111.
- Docker/PostgreSQL is not required for this unit-test scope, but the full application environment remains unavailable until Docker Desktop starts successfully.

### Edge cases

- PII at the beginning or end of a string and multiple generated values in one message.
- Case variations, punctuation, separators, and optional country-code prefixes for supported formats.
- Near-miss values that should remain unchanged when they do not match a supported pattern.
- Empty, whitespace-only, and non-PII text should remain unchanged.
- Re-running `scrub()` on already scrubbed text should not introduce additional changes.

This is a Week 8 planning artifact. The Hypothesis strategies and implementation are intentionally deferred to the later implementation week.
