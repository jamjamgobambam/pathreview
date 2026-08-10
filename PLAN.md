## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has text: None
https://github.com/ascherj/pathreview/issues/153

### Understand

The root cause is in `FaithfulnessChecker().check()` method which builds context string via `.get("text", "")` for each context chank. `.get()`'s default applies only if key is missing and not when key is exist but its value is `None`. When we passed chunk `{"text": None}` then `.get("text", "")` would return `None`, instead of empty string and later via `.join(...)` we get `TypeError` message because `join()` requires all inputs to be strings.

#### Expected Behavior

`.check()` should treat a `None` as empty string or missing one so that checker sent valid score output.

#### Actual Behavior

`.check()` crashes the code with `TypeError` message: `sequence item 0: expected str instance, NoneType found`

### Map

- `rag/evaluator/faithfulness_checker.py` which contains `FaithfullnessChecker.check()` and its buggy context-building logic
- `tests/unit/test_faithfulness_checker.py` which contains `test_none_context_chunk_text` test that currently fails

### Plan

1. Find exact line in `.check()` (in `rag/evaluator/faithfulness_checker.py`) where `chunk.get("text" "")` is called.
2. Replace it with the version that also catches a `None` such as `.get("text")` or ""
3. Check the rest of the file for having same `.get("text", "")` pattern in case if the same bug happened elsewhere in the class
4. Run `test_none_context_chunk_text` and see if it passes or not.
5. Run the full test (a.k.a. `pytest tests/unit/test_faithfulness_checker.py -v`) file to confirm that we don't have deterioated existing tests.

### Inputs & outputs

#### Input

The list of context string, where each chunk may have missing "text", empty string "" or "None"

#### Output

The context string that was built from all valid chunks (with missing "text" / "" / "None") would be treated as empty strings without calling `TypeError`. The `.check()` method should return correct score feedback from 0.0 to 1.0, even if chunk's input is distorted

### Risks & unknowns

- Unsure, whether on the same class file we have other methods that have identical `.get("text" "")` pattern.
- Unsure, whether we need a separate handling when "text" is a number because issue only mentions about `None`
- Unsure, whether the fix would change score behavior for chunks that have already valid text

### Edge cases

`{"text": None}` - should be treated as empty string or missing one
`{}` - should work through `.get()` default and treated as having empty text.
`{"text" ""}` - already empty string and should be uneffected by fix
A entirely empty `context_chunks` list - `.check()` confirms succefully and returns a valid score
