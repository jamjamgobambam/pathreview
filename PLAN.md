## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has text: None
https://github.com/ascherj/pathreview/issues/153

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The issue happens in `rag/evaluator/faithfulness_checker.py` when function `check()` builds `context_text` from chunk text values. The code assumes every chunk has a string `text`, but a chunk can contain `{"text": None}` for now. In that case, the join step raises a `TypeError` instead of treating the value as empty content. The expected behavior is for `None` text values to be handled safely so the faithfulness check can continue and return normally but currently only when "text" key is missing, the default applies. So, the variable chunk represents each dictionary in the context_chunks list. When a chunk contains {"text": None}, chunk.get("text", "") returns None because the key exists. This causes " ".join(...) to receive a None value instead of a string, resulting in a TypeError.


### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- `rag/evaluator/faithfulness_checker.py`
- `tests/unit/test_faithfulness_checker.py`

### Plan

1. Locate where `context_text` is built in `FaithfulnessChecker.check()`.
2. Update the context-building logic so that any `None` value for `chunk["text"]` is handled safely before calling `" ".join(...)`. This could mean treating `None` as an empty string or skipping it entirely if the "text" is None.
3. Add or update the test in `tests/unit/test_faithfulness_checker.py` to verify that `{"text": None}` no longer causes a `TypeError`.
4. Run the relevant unit tests to confirm the bug is fixed and that existing behavior for valid string inputs has not changed.


### Inputs & outputs
What does your fix take as input? What should it produce or change?
**Inputs:**
- A feedback string (`feedback`).
- A list of context chunks (`context_chunks`), where each chunk is a dictionary that may contain a `"text"` field. The `"text"` value can be a string, `None`, or the key may be missing.

**Outputs:**
- A faithfulness score between `0.0` and `1.0`.
- The function should no longer raise a `TypeError` when a chunk contains `{"text": None}`.
- `None` text values should be treated as empty strings (or skipped) so that the context can be built successfully and the faithfulness check completes normally.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- Changing the context-building logic in `rag/evaluator/faithfulness_checker.py` could unintentionally change how valid context chunks are combined, which might affect the faithfulness score.
- I need to verify whether other parts of the project expect every `text` value to always be a string.
- I also need to confirm that handling `None` values does not cause any existing unit tests to fail.

### Edge cases
What inputs or states should your fix handle gracefully?

- A context chunk with `{"text": None}` should not cause a `TypeError`.
- A context chunk with `{"text": ""}` (an empty string) should still work correctly.
- A context chunk that does not contain the `"text"` key should continue to be handled gracefully.
- A list containing both valid strings and `None` values (for example, `{"text": "Python"}`, `{"text": None}`, `{"text": "AI"}`) should still build the context correctly without crashing.