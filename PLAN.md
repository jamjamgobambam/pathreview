## Solution plan

**Issue:** Add integration tests for the full safety middleware chain (https://github.com/ascherj/pathreview/issues/75)

### Understand
When processing user feedback or input, the application relies on four safety components: `PromptDefense`, `ContentFilter`, `BiasDetector`, and `PIIScrubber`. Currently, each component has standalone unit tests in `tests/unit/`, but there is no integration test verifying the end-to-end flow. If an issue occurs where the `ContentFilter` incorrectly mutates a string that breaks the `PIIScrubber`, or if the chain is run in the wrong order, we wouldn't catch it. 

The expected behavior: create an integration test that manually constructs this pipeline sequence (`PromptDefense` -> `ContentFilter` -> `BiasDetector` -> `PIIScrubber`) and verifies that a single payload successfully traverses all layers (happy path), gets mutated correctly (scrubbed/filtered), or gets rejected at the appropriate layer (e.g. injection blocked immediately).

**Root cause:** Missing end-to-end integration test coverage for the sequential safety pipeline.

### Map
Files I expect to touch:
- `tests/integration/test_safety_integration.py` — I will write the new test suite here.
- `safety/prompt_defense.py`, `safety/content_filter.py`, `safety/bias_detector.py`, `safety/pii_scrubber.py` — I will reference these classes to understand their exact signatures (`is_injection_attempt`, `filter`, `detect_bias`, `scrub`).

### Plan
1. Open `tests/integration/test_safety_integration.py` and import all four safety classes.
2. Write a helper function `run_safety_pipeline(text: str)` inside the test file that simulates the intended production order:
   - Check `PromptDefense.is_injection_attempt(text)`. Raise `ValueError` if true.
   - Run `text, _ = ContentFilter.filter(text)`.
   - Check `BiasDetector.detect_bias(text)`. Raise `ValueError` if true.
   - Run `text = PIIScrubber().scrub(text)`.
   - Return the final text.
3. Write `test_safety_pipeline_happy_path`: Pass a normal text with some PII. Verify no ValueError is raised and the PII is `[REDACTED]`.
4. Write `test_safety_pipeline_injection_blocked`: Pass a prompt injection text. Verify `ValueError` is raised immediately.
5. Run `pytest tests/integration/test_safety_integration.py` to confirm the tests pass.

### Inputs & outputs
**Function I'm testing:** A simulated pipeline integrating `PromptDefense`, `ContentFilter`, `BiasDetector`, and `PIIScrubber`.

**Happy path test I'll write:**
```python
def test_safety_pipeline_happy_path():
    """Pipeline should allow safe text and scrub PII."""
    input_text = "The bootcamp grad wrote great code. Contact him at john@example.com."
    
    # 1. PromptDefense (passes)
    assert not PromptDefense.is_injection_attempt(input_text)
    
    # 2. ContentFilter (passes without mutation)
    filtered_text, _ = ContentFilter.filter(input_text)
    
    # 3. BiasDetector (passes)
    is_biased, _ = BiasDetector.detect_bias(filtered_text)
    assert not is_biased
    
    # 4. PIIScrubber (mutates)
    scrubber = PIIScrubber()
    final_text = scrubber.scrub(filtered_text)
    
    assert "john@example.com" not in final_text
    assert "[REDACTED]" in final_text
```

### Risks & unknowns
1. **Pipeline Execution Order:** I am assuming the order is Injection -> Content -> Bias -> PII. If the production code eventually implements this differently (e.g. Bias before Content), the test might need restructuring.
2. **Exception Handling:** I'll use `ValueError` in the test helper to simulate a block, but the actual app might use a custom exception (e.g. `SafetyError`). I'll need to adapt the test if a `core/exceptions.py` standard emerges.

### Edge cases
- **Multi-violation payloads:** A payload containing *both* a prompt injection attack and biased language. The test should verify it gets blocked by `PromptDefense` first and never reaches `BiasDetector`.
- **Empty strings:** How does the pipeline handle `""`? It should pass through gracefully without crashing any of the regex engines.
