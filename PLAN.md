## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` (#153)
https://github.com/ascherj/pathreview/issues/153

### Understand
`check()` builds a combined context string with `chunk.get("text", "")` for
each chunk in `context_chunks`. Python's `dict.get(key, default)` only
returns `default` when `key` is absent - if the key exists but its value is
`None`, `.get()` returns `None`. When a chunk is `{"text": None}`, the list
comprehension produces `[None]`, and `" ".join([None])` raises `TypeError:
sequence item 0: expected str instance, NoneType found`. Expected behavior:
the checker should treat a `None` text value the same as an empty string and
return a valid faithfulness score (a float between 0.0 and 1.0) instead of
crashing.

### Map
- `rag/evaluator/faithfulness_checker.py` - the `check()` method, specifically
  the context-concatenation line (~line 34). This is the only file that needs
  a code change.
- `tests/unit/test_faithfulness_checker.py` - contains the two relevant
  existing tests: `test_none_context_chunk_text` (currently failing) and
  `test_missing_text_key_in_chunk` (currently passing). No new test file is
  needed, but I'll re-run the full suite to check for regressions.

### Plan
1. Reproduce the crash locally and confirm via the existing failing test
   (done - see reproduction commit).
2. Change `chunk.get("text", "")` to `chunk.get("text") or ""` so that both a
   missing key and a `None` value fall through to an empty string.
3. Run `test_none_context_chunk_text` and `test_missing_text_key_in_chunk`
   together to confirm both pass.
4. Run the full test suite (`make test-unit`) to check for regressions in
   other tests that call `check()`.
5. Search the codebase for other `.get("text", ...)` or similar patterns on
   chunk dictionaries (e.g. in ingestion or other RAG modules) to see if the
   same bug class exists elsewhere, and note any findings for a follow-up
   issue if they're out of scope for this fix.

### Inputs & outputs
- **Input:** `feedback: str` and `context_chunks: list[dict]`, where each
  dict may have a `"text"` key that is a string, `None`, or missing.
- **Output:** a `float` faithfulness score between 0.0 and 1.0, computed the
  same way as today, but without crashing when `text` is `None`.

### Risks & unknowns
- Using `or ""` will also treat an existing empty string `""` as falsy and
  fall through to `""` - this is a no-op for that case, so it should be safe,
  but worth double-checking no test relies on distinguishing `""` from a
  missing/`None` value.
- Unsure whether similar `.get("text", ...)` patterns exist in other files
  (e.g. `ingestion/` or other evaluator modules) - if so, this fix wouldn't
  cover them, and that may be worth flagging as a separate issue rather than
  expanding scope here.
- `make check` (ruff/black/mypy) needs to pass on the changed line - low risk
  since it's a small change, but I'll confirm before opening the PR.

### Edge cases
- `{"text": None}` - the reported bug case, must return a valid float.
- `{"content": "..."}` (missing `"text"` key entirely) - already passes today,
  must keep passing.
- `{"text": ""}` - empty string value, should behave the same as before (no
  regression).
- Multiple chunks where some have `None` and others have valid text - should
  still concatenate correctly, skipping only the `None` ones' contribution to
  empty string.