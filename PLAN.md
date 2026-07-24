## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has text: None [#153](https://github.com/ascherj/pathreview/issues/153)

### Understand
`check()` in `faithfulness_checker.py` builds context text using `chunk.get("text", "")`. The `.get()` default only applies when the key is missing entirely. When the key is present but set to `None`, `.get()` returns `None`, and the subsequent `" ".join(...)` raises a `TypeError` because `join` expects strings, not `NoneType`.

### Map
- `rag/evaluator/faithfulness_checker.py` — the `check()` method, specifically line 34 where `context_text` is built via list comprehension and `" ".join()`
- `tests/unit/test_faithfulness_checker.py` — contains the already-written failing test `test_none_context_chunk_text`, plus `test_missing_text_key_in_chunk` (which passes, confirming the missing-key path works)

### Plan
1. Open `rag/evaluator/faithfulness_checker.py` and locate the list comprehension on line 34 that builds `context_text`
2. Replace `chunk.get("text", "")` with `chunk.get("text") or ""` so that both missing keys and explicit `None` values resolve to an empty string
3. Run `test_none_context_chunk_text` to confirm it passes
4. Run the full `make test-unit` to confirm no regressions in other faithfulness checker tests
5. Search the codebase for other instances of `.get("text", "")` to check if the same pattern exists elsewhere and could cause the same bug

### Inputs & outputs
- **Input:** `check(feedback: str, context_chunks: list[dict])` where `context_chunks` may contain dicts with `"text": None`
- **Expected output:** A float score between 0.0 and 1.0 — chunks with `None` text should be treated as empty strings and not crash the method

### Risks & unknowns
- The `or ""` pattern treats both `None` and empty string `""` the same way — need to verify that `""` chunks already work correctly (the passing `test_missing_text_key_in_chunk` test suggests this is fine)
- Other files in `rag/` may use the same `.get("text", "")` pattern — grep for it to check if this is a codebase-wide issue or isolated to `faithfulness_checker.py`
- The fix must not change scoring behavior for valid chunks — only prevent the crash for `None` values

### Edge cases
- Chunk with `"text": None` (the reported bug — should return a score, not crash)
- Chunk with no `"text"` key at all (already handled — `test_missing_text_key_in_chunk` passes)
- Chunk with `"text": ""` (empty string — should work and contribute nothing to context)
- Mixed list: some chunks with valid text, some with `None` (should skip the `None` ones and score based on valid chunks)
- All chunks have `"text": None` (should behave like empty context — return 0.0)
