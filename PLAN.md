## Solution plan

**Issue:** [Add integration tests for the full safety middleware chain #75](https://github.com/ascherj/pathreview/issues/75)

### Understand

The `safety/` package ships four independent guards, each covered only by a
per-component unit test in `tests/unit/`:

- `PromptDefense` (`safety/prompt_defense.py`) — sanitizes input and flags
  prompt-injection attempts.
- `ContentFilter` (`safety/content_filter.py`) — redacts genuinely harmful
  phrases from generated text.
- `BiasDetector` (`safety/bias_detector.py`) — flags dismissive/demographic
  bias.
- `PIIScrubber` (`safety/pii_scrubber.py`) — redacts email, phone, SSN, and
  street addresses.

Coverage is uneven: `PromptDefense`, `BiasDetector`, and `PIIScrubber` each have
a unit test (`tests/unit/test_prompt_defense.py`, `test_bias_detector.py`,
`test_pii_scrubber.py`), but **`ContentFilter` has no unit test at all** —
nothing in `tests/` imports it. My integration fail-case for the content filter
will therefore be the first test to exercise that component.

**Expected:** a request that flows through all four guards in order
(Prompt Defense → Content Filter → Bias Detector → PII Scrubber) is verified
end to end — clean input passes untouched, and each guard catches/redacts/flags
its target category while running as part of the chain.

**Actual:** no test composes the guards. Their combined behavior (ordering, one
guard's output feeding the next, multiple guards tripping on one input) is
completely untested. `tests/integration/` contains only an empty `__init__.py`.

Root cause: the integration coverage was simply never written; this is a
test-coverage gap, not a runtime defect in the guards themselves.

### Map

Files I expect to touch:

- `tests/integration/test_safety_middleware.py` — **new**, the integration test
  (already scaffolded with a red reproduction marker).
- `tests/conftest.py` *or* a local fixture block — pass/fail fixture text for
  each layer (may reuse existing `sample_*` fixtures).

Files I will read but not modify:

- `safety/prompt_defense.py`, `safety/content_filter.py`,
  `safety/bias_detector.py`, `safety/pii_scrubber.py` — to confirm each guard's
  public method and return shape.
- `tests/unit/test_prompt_defense.py`, `test_bias_detector.py`,
  `test_pii_scrubber.py` — to match existing marker/fixture conventions.

### Plan

1. Define a small in-test pipeline helper that runs text through the four guards
   in the specified order, returning the transformed text plus a record of which
   guards fired (the issue scopes this to the four-guard chain only — no changes
   to `review_service._run_safety_checks`).
2. Add a **pass** fixture: clean input that every guard leaves untouched, and
   assert the output is unchanged and no guard fired.
3. Add a **fail** fixture per guard (injection string, harmful phrase, biased
   statement, PII-bearing text) and assert the correct guard catches/redacts/
   flags it while the chain still completes.
4. Add one combined case (e.g. PII **and** injection in one input) to prove the
   guards cooperate rather than only working in isolation.
5. Delete the reproduction marker test and run `pytest -m integration` green.

### Inputs & outputs

- **Input:** strings representing request/response text, supplied via pytest
  fixtures (clean, per-layer-tripping, and combined).
- **Output:** no production code changes — the deliverable is assertions. The
  test produces pass/fail results verifying transformed text and per-guard
  firing flags for each fixture.

### Risks & unknowns

- **Guard interfaces differ** — `filter()` returns `(text, was_filtered)`,
  `detect_bias()` returns `(bool, reason)`, `PIIScrubber` is instance-based
  while others are `@staticmethod`. The pipeline helper must adapt each; risk of
  wrong assumptions until I re-read all four files.
- **Ordering side effects** — `PromptDefense.sanitize` strips `< > { }`, which
  could alter later inputs; need to confirm a realistic order that doesn't mask
  a downstream guard.
- **Overlap** — one fixture may trip more than one guard (e.g. address text also
  matching a pattern), making "only guard X fired" assertions brittle. Fixtures
  must be chosen to isolate each layer.
- **Untested content filter** — `ContentFilter` has never been exercised by any
  test, so its real behavior (the `(filtered_text, was_filtered)` return shape,
  which phrases actually match) is unverified. I must confirm it against
  `safety/content_filter.py` directly rather than assuming it works, and its
  fail-case fixture may need more iteration than the other three.
- **Marker/config** — must use `@pytest.mark.integration`; unsure whether the
  integration marker pulls in Docker services via `conftest` — verify the test
  stays pure-Python and needs no DB/Redis.

### Edge cases

- Empty string / whitespace-only input (no guard should error).
- Input that trips multiple guards at once (combined case).
- Input where an earlier guard's redaction removes what a later guard would have
  matched (ordering-dependent).
- Clean input containing near-miss text (e.g. `user@` without a domain) that
  must **not** be flagged, to guard against false positives.
