## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None`
(https://github.com/ascherj/pathreview/issues/153)

### Understand
`FaithfulnessChecker.check()` in `rag/evaluator/faithfulness_checker.py`
(line 34) builds `context_text` via:
```python
context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])
```
`dict.get(key, default)` only substitutes `default` when `key` is missing
from the dict — not when the key exists but holds `None`. So a chunk shaped
like `{"text": None}` makes `.get("text", "")` return `None`, and
`" ".join(...)` throws `TypeError: sequence item 0: expected str instance,
NoneType found`. Expected behavior: a chunk with `text: None` should
contribute an empty string to `context_text` (same as a chunk with
`text: ""` or a missing `"text"` key), and `check()` should still return a
valid `float` score in `[0.0, 1.0]` instead of crashing.

### Map
- `rag/evaluator/faithfulness_checker.py` — `FaithfulnessChecker.check()`,
  line 34, the primary fix target.
- `tests/unit/test_faithfulness_checker.py` — contains
  `test_none_context_chunk_text` (the existing failing test, class
  `TestFaithfulnessChecker`) which defines the expected fixed behavior; I'll
  add new test cases in this same file/class.
- `ingestion/chunking/` (e.g. `structural_chunker.py`, referenced in issue
  #149) — the likely upstream source of chunk dicts; worth checking whether
  it can produce `{"text": None}` and whether that should be prevented
  further upstream too, or just tolerated here.
- Any other file using `.get("text", ...)` on a chunk dict — to be found via
  grep in step 1 below.

### Plan
1. Run `grep -rn '\.get("text"' rag/ ingestion/ agent/` to check whether the
   same `.get("text", "")`-on-possibly-None pattern exists in other RAG or
   ingestion modules besides `faithfulness_checker.py`.
2. Fix line 34 in `faithfulness_checker.py` by changing 
   `chunk.get("text", "")` to `chunk.get("text") or ""`, so a `None` value
   is coerced to an empty string before the `.join()` call.
3. Run `pytest tests/unit/test_faithfulness_checker.py -k test_none_context_chunk_text -v`
   to confirm the previously failing test now passes.
4. Add 2 new unit tests to `TestFaithfulnessChecker` covering the edge cases
   below (all-`None`-chunks, and mixed `None`/valid chunks) that the existing
   test file doesn't yet cover.
5. Run `pytest tests/unit/test_faithfulness_checker.py -v` (full file, all 22
   tests) to confirm no regressions in the other 21 currently-passing tests.

### Inputs & outputs
**Input:** `feedback: str` and `context_chunks: list[dict]`, where each dict
is expected to have a `"text"` key whose value should be a `str` but can
currently be `None`.
**Output before fix:** Raises `TypeError` at line 34 when any chunk's
`"text"` value is `None`.
**Output after fix:** Returns the same `float` faithfulness score (range
`0.0`–`1.0`, per the existing docstring) it would compute if the `None`-text
chunk were instead an empty-string chunk — i.e., that chunk contributes
nothing to `context_text`, but scoring proceeds normally for the rest.

### Risks & unknowns
- Need to confirm in `ingestion/chunking/structural_chunker.py` whether
  `None`-text chunks are an expected/valid output of chunking, or actually
  a separate upstream bug that should be reported/fixed there too — my fix
  in `faithfulness_checker.py` makes this method resilient either way, but
  scope for *this* PR is just the faithfulness checker, not the chunker.
- `_is_supported()` (line ~66) does `context.lower().split()` — if
  `context_text` ends up empty (e.g. all chunks have `None` text), need to
  verify this doesn't behave unexpectedly (empty `context_tokens` set should
  just mean zero overlap, but I want to confirm with a test rather than assume).
- Need to grep for other callers of `FaithfulnessChecker.check()` 
  (`grep -rn "FaithfulnessChecker" rag/ agent/`) to make sure nothing else
  depends on the crash behavior (unlikely, but worth a quick check).

### Edge cases
- A chunk with `"text"` key missing entirely — already handled correctly
  today via `.get()`'s default; must confirm the fix doesn't change this.
- A chunk with `"text": None` — the reported bug; after the fix, treated as
  an empty string contribution to `context_text`.
- A `context_chunks` list where **every** chunk has `"text": None` — should
  produce an empty `context_text` string and still return a valid float
  score (likely `0.0` for all claims, since nothing can be supported), not
  crash or return `None`.
- A mixed list, e.g. `[{"text": None}, {"text": "Python developer"}]` —
  should still correctly use the valid chunk's text for support-checking
  while the `None` chunk is safely ignored.