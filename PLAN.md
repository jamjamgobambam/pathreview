## Solution plan

**Issue:** [Faithfulness checker crashes when a context chunk has text: None]

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
A string is supposed to be returned instead of a NoneType. 

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
evaluator/faithfulness_checker.py
tests/unit/test_faithfulness_checker.py

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1. Reproduce the crash with a unit test: call `FaithfulnessChecker.check()` with a `context_chunks` entry like `{"text": None}` and confirm it raises (currently `chunk.get("text", "")` returns `None` when the key is present but its value is `None`, since `dict.get` only falls back to the default when the key is *missing*).
2. Fix `check()` (`rag/evaluator/faithfulness_checker.py:34-36`) to coerce `None` to `""`, e.g. `chunk.get("text") or ""`.
3. Add a regression test in `tests/unit/test_faithfulness_checker.py` covering a chunk with `text: None` mixed in with valid chunks, and one where *all* chunks have `text: None`.
4. Run the full faithfulness test file to confirm no other tests regressed.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
Input: `context_chunks: list[dict]`, where individual chunk dicts may have `"text"` missing, `None`, or a non-empty string. Output: `check()` should still return a float in `[0.0, 1.0]` without raising, treating a chunk with `text: None` the same as an empty-text chunk (i.e., it contributes nothing to `context_text`).

### Risks & unknowns
What could go wrong? What are you still unsure about?
- Other chunk fields (not just `"text"`) might also be `None` elsewhere in the pipeline and hit the same bug — worth grepping for other `chunk.get(...)` calls upstream/downstream.
- Unclear whether `None` text should be logged/flagged as a data-quality issue upstream (empty retrieval) vs. silently ignored here.
- Need to confirm callers never rely on `check()` raising to catch malformed input elsewhere.

### Edge cases
What inputs or states should your fix handle gracefully?
- `context_chunks` where every chunk has `text: None` (should behave like `context_chunks=[]` in terms of not crashing, likely scoring all claims unsupported).
- Mixed list with some `None` and some valid text chunks.
- Chunk dict missing the `"text"` key entirely (already handled today, should remain unchanged).
- `text` present but an empty string `""` (already handled today).