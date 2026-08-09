# Solution Plan

**Issue:** #153 — Faithfulness checker crashes when a context chunk has `text: None`  
**Issue link:** https://github.com/ascherj/pathreview/issues/153

---

## Understand

The issue occurs in `FaithfulnessChecker.check()` in `rag/evaluator/faithfulness_checker.py`. The method builds a single context string by retrieving the `text` value from each context chunk with `chunk.get("text", "")` and passing those values to the `" ".join()` call.

The default value `""` only handles chunks where the `text` key is missing. If the `text` key exists but its value is `None`, `chunk.get("text", "")` returns `None`. Python's `" ".join()` expects every item to be a string, so it raises:

```text
TypeError: sequence item 0: expected str instance, NoneType found
```

I reproduced this behavior locally using the existing `test_none_context_chunk_text` unit test.

The expected behavior is for `FaithfulnessChecker.check()` to handle a context chunk containing `text: None` gracefully instead of crashing. The checker should continue to return a valid faithfulness score between `0.0` and `1.0`.

**Root cause:** `FaithfulnessChecker.check()` assumes every retrieved context chunk contains a string value for the `text` field. When a chunk contains `{"text": None}`, the value is passed directly to the `" ".join()` call, which only accepts strings and therefore raises a `TypeError`.

---

## Map

### Files and functions involved

### `rag/evaluator/faithfulness_checker.py`

- `FaithfulnessChecker.check()` is the location of the failure and the primary function expected to be modified.
- The context text is constructed here before individual feedback claims are evaluated.

### `tests/unit/test_faithfulness_checker.py`

- Contains the existing `test_none_context_chunk_text` test that reproduces Issue #153.
- Also contains `test_missing_text_key_in_chunk`, which verifies behavior when a chunk does not contain a `text` key.
- I will use the existing test patterns to verify the fix and determine whether additional edge-case coverage is needed.

### `rag/evaluator/eval_suite.py`

- `EvalSuite.run()` passes `feedback` and retrieved `chunks` to `self.faithfulness_checker.check(feedback, chunks)`.
- I do not currently expect to modify this file, but it is part of the execution path and will be considered when verifying that the fix preserves the evaluation flow.

### Data flow

```text
EvalSuite.run()
        │
        ▼
FaithfulnessChecker.check(feedback, chunks)
        │
        ▼
Context text construction
        │
        ▼
Claim support checks
        │
        ▼
Faithfulness score
        │
        ▼
EvalResult
```

---

## Plan

1. Review the context-building logic in `FaithfulnessChecker.check()` and confirm the difference between:
   - a missing `text` key,
   - an explicit `text: None` value,
   - and a valid string value.

2. Update the context construction in `rag/evaluator/faithfulness_checker.py` so that an explicit `None` text value is handled safely before values are passed to the `" ".join()` call while preserving valid string content.

3. Run the existing `test_none_context_chunk_text` unit test to verify that the original `TypeError` no longer occurs and that the method returns a valid `float` score between `0.0` and `1.0`.

4. Run the related faithfulness checker unit tests, including the missing-`text`-key and normal string-context cases, to confirm that the change does not regress existing behavior.

5. Add or refine unit-test coverage in `tests/unit/test_faithfulness_checker.py` if the existing tests do not sufficiently cover mixed chunks containing valid strings, `None`, empty strings, or missing `text` keys.

6. Run the project's relevant tests and quality checks to verify that the focused change does not introduce regressions or formatting/type-checking problems.

---

## Inputs & Outputs

**Function expected to change**

```python
FaithfulnessChecker.check(feedback: str, context_chunks: list[dict]) -> float
```

### Expected inputs

- `feedback`: Generated feedback containing claims to evaluate.
- `context_chunks`: A list of dictionaries containing valid string values under the `text` key.

### Expected output

- A `float` faithfulness score between `0.0` and `1.0`.

### Problem input

```python
{"text": None}
```

### Current behavior

The `" ".join()` call receives a `None` value and raises:

```text
TypeError: sequence item 0: expected str instance, NoneType found
```

### Expected behavior after the fix

- A chunk containing `text: None` is handled safely.
- `FaithfulnessChecker.check()` does not raise a `TypeError`.
- The method continues its normal evaluation logic and returns a valid `float` score between `0.0` and `1.0`.

### Primary verification

- `test_none_context_chunk_text` should pass after the implementation.

---

## Risks & Unknowns

1. **How `None` should affect faithfulness scoring**

   The issue clearly requires preventing the crash, but I also need to preserve the intended scoring behavior. Before implementing the fix, I will inspect how empty strings and missing `text` keys are currently handled in both `FaithfulnessChecker.check()` and the existing unit tests.

2. **Mixed context chunks**

   A list may contain both valid text chunks and chunks whose `text` value is `None`. The fix must preserve valid context while safely handling invalid values. I will verify this behavior using the existing tests and add focused coverage if necessary.

3. **Unexpected non-string values**

   Issue #153 specifically concerns `None`. Other values such as integers or lists could also cause the `" ".join()` call to fail, but broad type coercion may hide upstream data-quality problems. Unless the project's expected chunk contract indicates otherwise, I will keep the implementation scoped to the reported issue.

4. **Regression in existing scoring behavior**

   Changing the context-construction logic could affect `_is_supported()` results and therefore alter faithfulness scores. After implementing the fix, I will run the complete `tests/unit/test_faithfulness_checker.py` suite to verify that existing scoring behavior remains unchanged.

---

## Edge Cases

- A single context chunk containing `{"text": None}` should not crash.
- A context chunk with no `text` key should continue to be handled gracefully.
- A context chunk containing `{"text": ""}` should continue to be handled without error.
- Multiple chunks containing a mixture of valid strings and `None` values should preserve the valid text and not crash.
- Multiple chunks where every `text` value is `None` should still return a valid score rather than raising a `TypeError`.
- Valid context chunks containing normal strings should retain their existing behavior and scoring.
- An empty `context_chunks` list should continue to return `0.0` according to the existing early-return behavior.