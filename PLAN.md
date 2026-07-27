## Solution plan

**Issue:** [Add integration tests for the full safety middleware chain](https://github.com/ascherj/pathreview/issues/75)

### Understand

The four safety components exist and have independently callable APIs, but the
repository has no integration test that applies them to the same request in the
documented order: prompt defense, content filtering, bias detection, then PII
scrubbing. `tests/integration/` currently contains only `__init__.py`, so pytest
collects no integration tests and cannot detect ordering, short-circuit, or
transformation-preservation regressions across the safety stack.

Expected behavior is for representative clean input to pass through every layer
without being altered, while targeted unsafe input is detected, filtered,
flagged, or redacted by the appropriate layer. Actual behavior is only asserted
one component at a time, and `ContentFilter` has no dedicated test coverage.

### Map

The implementation should add:

- `tests/integration/test_safety_middleware.py`
  - Mark the tests with `pytest.mark.integration`.
  - Define reusable clean, injection, harmful-content, biased-language, and PII
    fixtures.
  - Add a small test-local helper or fixture that invokes the public APIs in the
    documented order and preserves each layer's result for assertions.
  - Cover pass and fail behavior for all four layers plus one combined request.

The tests will exercise, but should not initially modify:

- `safety/prompt_defense.py`
  - `PromptDefense.is_injection_attempt()` and `PromptDefense.sanitize()`
- `safety/content_filter.py`
  - `ContentFilter.filter()`
- `safety/bias_detector.py`
  - `BiasDetector.detect_bias()`
- `safety/pii_scrubber.py`
  - `PIIScrubber.scrub()` and, if useful for assertions,
    `PIIScrubber.detect()`

`tests/conftest.py` should remain unchanged unless a fixture proves useful
outside this one integration module.

### Plan

1. Add `tests/integration/test_safety_middleware.py` with
   `pytest.mark.integration`, focused fixtures, and a test-local representation
   of the result from each safety layer.
2. Add a clean-input test asserting that prompt defense does not flag the
   request, content filtering and bias detection remain false, PII scrubbing
   leaves the text unchanged, and the final output matches the input.
3. Add focused fail-case tests for prompt injection, harmful content, biased
   language, and email PII. Assert each component's native contract: detection
   flag, reason, replacement marker, or redacted output.
4. Add a combined-input test proving that earlier transformations are preserved
   when the same text proceeds through later layers—for example, harmful content
   stays removed while an email is also redacted.
5. Run the new integration module, the four relevant safety test modules, and
   repository quality checks. Keep unrelated pre-existing unit failures
   documented rather than expanding issue #75 into fixes for those components.

### Inputs & outputs

The tests take plain-text request or feedback strings as input:

- clean portfolio feedback
- a prompt-injection string containing a role switch
- harmful feedback matching `ContentFilter.HARMFUL_PATTERNS`
- biased feedback matching a documented bias pattern
- text containing an email address
- a combined harmful-content and PII example

The expected outputs are the components' existing public return values:

- a prompt-injection boolean and sanitized text
- filtered text plus `was_filtered`
- `is_biased` plus a non-empty reason
- final text with PII replaced by `[REDACTED]`

The integration assertions should also retain a final transformed string so the
test can prove that sequential layers do not undo earlier filtering.

### Risks & unknowns

- There is no production `SafetyMiddleware` or pipeline object. A test-local
  composition can verify the requested order, but it will not prove that an API
  route uses that order. Before changing production code, confirm whether issue
  #75 intends only the named integration-test file.
- The components expose different return shapes and do not define a shared
  rejection policy. Prompt injection and bias may be flags rather than automatic
  hard failures, so tests should assert current contracts instead of inventing
  HTTP responses.
- The existing component baseline currently has 15 failures involving prompt
  spacing, bias patterns, and PII matching. New fixtures should use known,
  contract-supported examples so issue #75 does not absorb unrelated fixes.
- Transformation order matters. Sanitizing or filtering text before another
  detector could remove the evidence that detector expects, so each layer's
  result and the final output need separate assertions.

### Edge cases

- empty and whitespace-only input
- clean multiline text that should not resemble a role-switch injection
- case-insensitive injection, harmful-content, and bias patterns
- text containing more than one unsafe category
- multiple PII values while preserving ordinary technical content
- already sanitized, filtered, or redacted text to check idempotence
- content where an earlier replacement marker must survive later layers
