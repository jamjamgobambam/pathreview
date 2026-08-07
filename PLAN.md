## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` — https://github.com/ascherj/pathreview/issues/153

### Understand
`FaithfulnessChecker.check()` scores generated feedback against retrieved
context chunks. It builds the comparison text with:

```python
context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])
```

The root cause is the `dict.get(key, default)` gotcha: the `""` default only
applies when the `"text"` key is *absent*. When a chunk carries an explicit
`"text": None` (e.g. a source whose text failed to extract during ingestion),
`.get("text", "")` returns `None`, and `" ".join([...])` raises
`TypeError: sequence item 0: expected str instance, NoneType found`.

- **Expected:** the checker degrades gracefully — a `None`-text chunk is
  treated as empty and contributes nothing, returning a float score in
  `[0.0, 1.0]`.
- **Actual:** the entire evaluation run crashes with a `TypeError`.

Reproduced locally with `scripts/repro_issue_153.py` and the existing (failing)
unit test `test_none_context_chunk_text`.

### Map
Files/functions involved:

- `rag/evaluator/faithfulness_checker.py` — `FaithfulnessChecker.check()`, the
  list comprehension at ~line 33-35 (the single line to fix).
- `tests/unit/test_faithfulness_checker.py` — `test_none_context_chunk_text`
  (already present, currently failing) and `test_missing_text_key_in_chunk`
  (guards the absent-key path); assert graceful behavior here.
- `scripts/repro_issue_153.py` — standalone reproduction (added this week).

### Plan
1. Change `chunk.get("text", "")` to `chunk.get("text") or ""` so both a
   missing key and an explicit `None` (and other falsy text) coerce to `""`.
2. Confirm `test_none_context_chunk_text` now passes and add an assertion that
   a `None`-text chunk scores the same as an empty-string chunk (no crash,
   valid float).
3. Run the full `tests/unit/test_faithfulness_checker.py` suite to confirm no
   regression on the existing supported/unsupported/partial cases.
4. Re-run `scripts/repro_issue_153.py` to confirm it now prints a score
   instead of raising.

### Inputs & outputs
- **Input:** `feedback: str` and `context_chunks: list[dict]`, where a chunk's
  `"text"` value may be a normal string, an empty string, missing, or `None`.
- **Output:** a `float` faithfulness score in `[0.0, 1.0]`. After the fix, a
  `None`-text chunk contributes an empty string to `context_text` instead of
  raising. No change to the return type or the scoring math for valid chunks.

### Risks & unknowns
- **Behavior change vs. crash:** callers currently relying on the crash to
  signal bad ingestion data would silently get a score instead. Low risk —
  the issue explicitly asks for graceful degradation, and malformed chunks
  should not abort a whole evaluation run.
- **Other `None` shapes:** a chunk could be `None` itself, or `"text"` could be
  a non-string (e.g. int). `chunk.get("text") or ""` handles falsy values but
  not a truthy non-string; I'll confirm whether ingestion can ever produce
  those before deciding to widen the coercion (likely out of scope).
- **Upstream duplication:** verify no other module builds context with the same
  `.get("text", "")` pattern that would need the same fix (grep the `rag/`
  package).
  - Confirmed via `grep -rn 'get("text"' rag/`: three other call sites share
    the pattern — `rag/evaluator/relevance_scorer.py:32`,
    `rag/generator/review_generator.py:157`, and
    `rag/retriever/hybrid.py:85`.
  - `review_generator.py` and `hybrid.py` don't crash on `None` (an f-string
    just renders the literal text `"None"`; `hybrid.py` merely stores the
    value), so they're a data-quality smell, not a `TypeError`.
  - `relevance_scorer.py` *does* crash the same class of bug: `text =
    chunk.get("text", "")` feeds into `_tokenize(text)`, which calls
    `text.lower().split()` — a `None` value raises `AttributeError:
    'NoneType' object has no attribute 'lower'` instead of the faithfulness
    checker's `TypeError`, but the underlying gotcha is identical.
  - Decision: out of scope for issue #153, which is specifically about the
    faithfulness checker. Filing this as a separate follow-up rather than
    widening this PR, per the "one small method in one file" scope from the
    Week 7 scope check.

### Edge cases
- Chunk with `"text": None` → treated as empty, no crash.
- Chunk missing the `"text"` key entirely → still `""` (unchanged behavior).
- Chunk with `"text": ""` → empty, contributes nothing.
- Mixed list: some valid-text chunks and some `None`-text chunks → scores using
  only the valid text.
- All chunks have `None`/empty text → `context_text` is `""`, so no claims are
  supported and the score is `0.0` (no crash).
