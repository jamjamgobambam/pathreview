# Week 8 — Issue Reproduction & Solution Planning

## Issue

**Issue:** #111 — No property-based tests for the PII scrubber

**Issue link:** https://github.com/ascherj/pathreview/issues/111

**Branch:** `test/111-pii-scrubber-property-tests`

## Reproduction

### Expected Behavior

The PII scrubber test suite should use property-based tests to generate many valid examples of
every supported PII category and verify that each value is removed. The tests should exercise the
public `PIIScrubber.scrub()` behavior without copying its regular expressions into the generators.

### Actual Behavior

Before this change, `tests/unit/test_pii_scrubber.py` contained only example-based tests with a
small set of hard-coded values. The scrubber supported email addresses, US phone numbers, compact
international phone numbers, Social Security numbers, and US street addresses, but no Hypothesis
strategies generated variations of those values.

### Steps to Reproduce

1. Open `tests/unit/test_pii_scrubber.py`.
2. Search for imports from `hypothesis`, `@given`, or custom Hypothesis strategies.
3. Confirm that the file contains example-based tests but no property-based tests.
4. Open `safety/pii_scrubber.py` and identify the five configured PII categories.
5. Confirm that `hypothesis` is already included in the `dev` dependency group in
   `pyproject.toml`.

## Root Cause

The existing suite was written around selected examples. It did not include independently
constructed generators capable of exercising meaningful variations within the scrubber's current
supported formats.

## Solution Plan

### Files to Change

- `tests/unit/test_pii_scrubber.py`
- `PLAN.md`
- `JOURNAL.md`

### Implementation Steps

1. Inspect the scrubber implementation, existing tests, dependency configuration, and test style.
2. Define the supported formats and `[REDACTED]` replacement contract.
3. Create bounded component-based strategies for emails, US phones, international phones, SSNs,
   and street addresses.
4. Add one primary property per category verifying complete redaction and preservation of known
   safe surrounding text.
5. Add an idempotence property for generated PII.
6. Add a robustness property for reasonably sized arbitrary Unicode strings.
7. Run the focused property tests and review any minimized failing examples.
8. Constrain generators when a case falls outside the current fully supported contract rather
   than changing production behavior for a test-only issue.
9. Run formatting, linting, diff, and focused test checks and document pre-existing failures.

## Risks and Edge Cases

- Generators must not duplicate the implementation regexes because that would make the tests
  unable to catch many regex defects.
- Generated values must stay within formats the current implementation fully redacts.
- Merely asserting that the original string disappeared can allow partial redaction to pass, so
  primary properties should verify the complete expected output.
- Phone patterns can overlap because US phone redaction runs before international phone redaction.
- Some address suffix alternatives partially match longer suffixes, so generated suffixes should
  be limited to values that the current behavior replaces completely.
- Strategies must remain bounded so normal Hypothesis runs stay fast in CI.
- Existing test, lint, and type-check failures must be recorded separately from failures introduced
  by this change.

## Verification Plan

- Run the new properties with:
  `python -m pytest tests/unit/test_pii_scrubber.py -q -k "generated or bounded"`.
- Run the complete PII scrubber test file and document pre-existing failures.
- Run Black against `tests/unit/test_pii_scrubber.py`.
- Run Ruff against the changed test file and distinguish existing findings from new findings.
- Run `git diff --check`.
- Review the final diff and confirm that production code and dependencies remain unchanged.
