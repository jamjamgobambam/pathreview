## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has text: None #153
**Link:** https://github.com/ascherj/pathreview/issues/153

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The root cause is `chunk.get("text", "")` in `FaithfulnessChecker.check()`: the `""` default only applies when the `text` key is missing, so a present-but-null value (`{"text": None}`) returns `None`. That `None` reaches `" ".join(...)`, which requires all items to be strings. Expected: the checker coerces null text and returns a valid float score; actual: it raises `TypeError: sequence item 0: expected str instance, NoneType found`.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- `rag/evaluator/faithfulness_checker.py` — the `check()` method, specifically the context-concatenation list comprehension at lines 34–36.
- `tests/unit/test_faithfulness_checker.py` — already contains the failing `test_none_context_chunk_text` that reproduces the bug and will verify the fix.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Replace `chunk.get("text", "")` with `chunk.get("text") or ""` so both missing and null values coerce to an empty string.
2. Run `test_none_context_chunk_text` to confirm it now passes.
3. Run the full `test_faithfulness_checker.py` suite to ensure no regressions.
4. Commit the fix on branch `fix/153-rag-chunk-error` and open a PR referencing issue #153.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

Input: `feedback` (str) and `context_chunks` (list of dicts) where a chunk's `text` may be missing, `None`, or a string. Output: a faithfulness score as a float in `[0.0, 1.0]`, with null/missing chunk text treated as empty and never crashing.

### Risks & unknowns
What could go wrong? What are you still unsure about?

Using `or ""` also converts other falsy values (e.g. `0` or `False`) to empty strings, which is fine here since `text` is expected to be a string. Overall risk is low since the change is one line covered by existing tests; the main unknown is whether any caller relies on the current crashing behavior, which is unlikely.

### Edge cases
What inputs or states should your fix handle gracefully?

`{"text": None}` (present but null), `{"content": "..."}` (missing `text` key), and multiple chunks mixing valid text with null/missing values. All should produce a valid float score without raising.