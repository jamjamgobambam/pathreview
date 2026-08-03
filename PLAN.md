## Solution plan

**Issue:** [Faithfulness checker can never mark short claims as supported](https://github.com/ascherj/pathreview/issues/152)

### Understand

The faithfulness checker extracts claims from generated feedback, compares them with retrieved context, and returns a score representing how many claims are supported.

The expected behavior is that short factual claims should be marked as supported when their meaningful terms appear in the context. For example:

```python
feedback = "Knows Python. Knows SQL."
context_chunks = [
    {"text": "python expert"},
    {"text": "sql expert"},
]
```

This input should receive a score of `1.0` because both claims are supported by the context.

The actual result is `0.0`. The reproduction test also reports `claims_count=1`, even though the feedback contains two claims.

The current implementation appears to have two related problems:

1. `_is_supported()` requires at least two meaningful tokens to overlap between a claim and the context. A short claim such as `"Knows Python"` may contain only one meaningful token, `python`, so it cannot meet the current threshold.

2. `_extract_claims()` appears to discard one of the short claims. I need to inspect its length and sentence-filtering rules to confirm why only one claim is counted.

### Map

The main files and functions involved are:

- `rag/evaluator/faithfulness_checker.py`
  - `FaithfulnessChecker.check()`
  - `FaithfulnessChecker._extract_claims()`
  - `FaithfulnessChecker._is_supported()`

- `tests/unit/test_faithfulness_checker.py`
  - Existing faithfulness checker tests
  - The new reproduction test for short supported claims
  - Additional regression tests for supported, unsupported, and partially supported short claims

I do not currently expect to change the frontend, database, or other RAG modules.

### Plan

1. Inspect `_extract_claims()` to determine why `"Knows Python. Knows SQL."` produces only one extracted claim.

2. Update claim extraction so short but meaningful factual claims are not discarded.

3. Update `_is_supported()` so a short claim can be supported by one meaningful overlapping token, while longer claims still require stronger evidence.

4. Add regression tests for fully supported, partially supported, and unsupported short claims.

5. Run the targeted faithfulness checker tests and the full test suite to verify that the fix works without changing unrelated behavior.

### Inputs & outputs

The checker takes two inputs:

- `feedback`: a string containing one or more factual claims.
- `context_chunks`: a list of dictionaries containing retrieved supporting text.

Example input:

```python
feedback = "Knows Python. Knows SQL."
context_chunks = [
    {"text": "python expert"},
    {"text": "sql expert"},
]
```

The checker produces a floating-point faithfulness score between `0.0` and `1.0`.

Expected outputs include:

- All claims are supported: `1.0`
- No claims are supported: `0.0`
- Only some claims are supported: a score between `0.0` and `1.0`

The existing behavior for empty feedback or empty context should remain unchanged.

### Risks & unknowns

- Allowing one matching token could create false positives when the matching word is generic, such as `"skills"`, `"project"`, or `"experience"`.

- I need to determine how the checker should distinguish meaningful technical terms such as `"Python"` from generic words.

- I need to confirm the exact reason only one of the two reproduced claims is extracted.

- Changing claim extraction could affect the scores of longer or compound feedback statements.

- Splitting claims on punctuation or conjunctions could incorrectly separate phrases that should remain together.

- The support threshold may need to depend on the number of meaningful tokens in a claim rather than its raw character length.

### Edge cases

The fix should handle:

- A short claim with one meaningful matching token.
- A short claim with no matching tokens.
- Multiple short claims that are all supported.
- Multiple claims where only some are supported.
- Differences in capitalization, such as `"Python"` and `"python"`.
- Punctuation next to technical terms, such as `"Python,"` or `"SQL."`.
- Claims whose only overlapping words are stopwords.
- Generic one-word overlap that should not automatically count as support.
- Empty feedback.
- Empty context.
- Multiple separate context chunks.