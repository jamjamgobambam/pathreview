## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` — https://github.com/ascherj/pathreview/issues/153

### Understand
`FaithfulnessChecker.check()` builds `context_text` using
`chunk.get("text", "")`. Python's `dict.get(key, default)` only returns
the default when the key is *absent* — if the key exists but its value is
`None`, `.get()` returns `None` itself. When a chunk like `{"text": None}`
is passed in, this produces `None` in the list passed to `" ".join(...)`,
which raises `TypeError: sequence item 0: expected str instance, NoneType
found`. Expected behavior: chunks with `text: None` should be treated the
same as chunks with an empty or missing `text` field — contributing an
empty string to the context, not crashing.

### Map
- `rag/evaluator/faithfulness_checker.py` — the `check()` method, specifically
  the `context_text` construction line
- `tests/unit/test_faithfulness_checker.py` — `test_none_context_chunk_text`
  (already exists, currently failing) and `test_missing_text_key_in_chunk`
  (already passing, used to confirm the fix doesn't regress this case)

### Plan
1. Reproduce the crash locally and confirm `test_none_context_chunk_text` fails
2. Fix the line in `check()` to treat `None` values the same as missing keys —
   change `chunk.get("text", "")` to `chunk.get("text") or ""`
3. Run the full test suite to confirm `test_none_context_chunk_text` passes
   and no other tests regress
4. Add a code comment explaining why `or ""` is used instead of a plain
   default, since the reason (None vs missing key) isn't obvious at a glance
5. Update JOURNAL.md and push final commits

### Inputs & outputs
Input: `context_chunks`, a list of dicts that may contain `"text"` as a
string, `None`, or be missing entirely. Output: `context_text`, a single
joined string that should never be `None`, regardless of which of the
three input variants occurs.

### Risks & unknowns
- Need to confirm no other part of the codebase relies on `chunk.get("text", "")`
  returning `None` for some other conditional check — a quick repo-wide
  search for `.get("text"` will confirm this method is only used here
- Same pattern may exist elsewhere with other optional dict keys in the
  RAG pipeline — worth a quick grep for `.get(` with default `""` across
  `rag/` in case a similar bug hides elsewhere, though that's out of scope
  for this specific issue

### Edge cases
- `{"text": None}` → should contribute `""`, no crash (the reported bug)
- `{"content": "..."}` (key missing entirely) → should contribute `""`,
  no crash (already works, covered by existing passing test)
- `{"text": ""}` → should contribute `""` (already works)
- `{"text": "actual context"}` → should contribute the string unchanged
  (already works)
- Empty `context_chunks` list → already handled by the early return
  (`if not feedback or not context_chunks`)
