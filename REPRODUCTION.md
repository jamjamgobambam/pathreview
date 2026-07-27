# Issue #75 reproduction

**Issue:** [Add integration tests for the full safety middleware chain](https://github.com/ascherj/pathreview/issues/75)

**Reproduced on:** July 26, 2026

## Steps

1. Confirm the integration-test directory contains only its package marker:

   ```bash
   git ls-files tests/integration
   ```

   Observed output:

   ```text
   tests/integration/__init__.py
   ```

2. Ask pytest to run the integration suite:

   ```bash
   .venv/bin/pytest tests/integration -q
   ```

   Pytest exits with status 5 and reports `no tests ran`. In particular,
   `tests/integration/test_safety_middleware.py`, the file named by the issue,
   does not exist.

3. Search for code that composes the four safety components:

   ```bash
   rg -n "PromptDefense|ContentFilter|BiasDetector|PIIScrubber" \
     --glob '!safety/*.py' --glob '!tests/unit/test_*.py' .
   ```

   The search returns no matches. The components are implemented separately in
   `safety/prompt_defense.py`, `safety/content_filter.py`,
   `safety/bias_detector.py`, and `safety/pii_scrubber.py`, but no existing test
   or production path sends the same input through all four in order.

4. Exercise the four public APIs manually with clean and harmful/PII-bearing
   input. Each component responds independently: prompt defense returns a
   boolean, content filtering returns transformed text plus a flag, bias
   detection returns a flag plus a reason, and PII scrubbing returns transformed
   text. This confirms the individual pieces are callable but there is no
   integration contract asserting their combined behavior or ordering.

## Observed gap

The reported feature gap is reproducible: PathReview has no collected
integration tests and no coverage for the complete prompt-defense → content
filter → bias-detector → PII-scrubber flow. A regression in component ordering,
short-circuit behavior, or preservation of earlier transformations would not be
caught by an end-to-end safety-stack test.

As a baseline, running the three existing component unit-test files produced
`74 passed, 15 failed`. Those failures expose existing edge cases in prompt
spacing, bias patterns, and PII phone/address matching; they are not caused by
this reproduction commit and are outside issue #75's integration-test scope.
