## Solution plan

**Issue:** #153 — Faithfulness checker crashes when a context chunk has `text: None`
(https://github.com/ascherj/pathreview/issues/153)

### Understand
`FaithfulnessChecker.check()` builds context by pulling `chunk.get("text", "")` from
each context chunk and joining the results with `" ".join(...)`. `.get()` only applies
its default when the *key* is missing. If a chunk has `"text": None` (key present,
value `None`), `.get()` returns `None`, and `None` passed into `" ".join(...)` raises
`TypeError: sequence item 0: expected str instance, NoneType found`.

Expected behavior: a chunk with `text: None` should be treated as empty context (`""`)
and `check()` should return a normal float score without crashing. Actual behavior:
the checker raises an unhandled `TypeError`.

Confirmed via local reproduction:
```python
FaithfulnessChecker().check('Knows Python.', [{'text': None}])
# TypeError: sequence item 0: expected str instance, NoneType found
```
and via the existing (currently failing) test `test_none_context_chunk_text` in
`tests/unit/test_faithfulness_checker.py`.

### Map
- `rag/evaluator/faithfulness_checker.py` — `check()` method, line ~35, where context
  is built via `chunk.get("text", "")`
- `tests/unit/test_faithfulness_checker.py` — contains `test_none_context_chunk_text`
  (target test to make pass) and `test_missing_text_key_in_chunk` (already passing,
  covers the "key missing" case); may add further edge-case tests here

### Plan
1. Locate the exact line in `check()` where `chunk.get("text", "")` builds context.
2. Replace `chunk.get("text", "")` with `chunk.get("text") or ""` so both a missing
   key and an explicit `None` value fall back to an empty string.
3. Run `test_none_context_chunk_text` and `test_missing_text_key_in_chunk` and
   confirm both pass.
4. Add extra unit tests for adjacent edge cases: empty string `""`, whitespace-only
   text, and a mix of `None` and valid chunks in the same list.
5. Run the full test suite (`pytest`) to confirm no other tests relied on the old
   (buggy) behavior, and re-run `pre-commit` to confirm lint/format still pass.

### Inputs & outputs
- **Input:** a list of context chunk dicts, where each chunk may have `"text"` missing,
  `None`, an empty string, or a normal string.
- **Output:** `check()` should return a normal float faithfulness score (0.0–1.0)
  without raising, treating any missing/`None` `text` as an empty string contribution
  to the joined context.

### Risks & unknowns
- Need to confirm `chunk.get("text") or ""` doesn't unintentionally swallow other
  falsy-but-valid values (e.g., if `text` could legitimately be `0` or `False` —
  unlikely given it's expected to be a string).
- Found the identical `.get("text", "")` pattern in three other files:
  `rag/evaluator/relevance_scorer.py:32`, `rag/retriever/hybrid.py:85`, and
  `rag/generator/review_generator.py:157`. Each has the same latent bug (a chunk
  with `text: None` would crash them too), but issue #153 is scoped only to
  `faithfulness_checker.py`. Flagging this as a candidate for a follow-up issue/PR
  rather than expanding scope here.
- Pre-existing mypy failures (missing type annotations) affect the entire test
  file and exist on `main` independent of this change; confirmed via
  `pre-commit run mypy` on `main` before using `--no-verify` on the reproduction
  commit.

### Edge cases
- `chunk = {"text": None}` — should not crash, contributes `""` to context.
- `chunk = {}` (no `"text"` key at all) — should still work as before (already
  covered by `test_missing_text_key_in_chunk`, using a different wrong key).
- `chunk = {"text": ""}` — already works, confirm it still does after the fix.
- Multiple chunks in the list, some `None`, some valid strings — should join
  correctly, contributing `""` only for the `None` ones.
- `chunks = []` (empty list entirely) — should not be broken by this change
  (already covered by `test_empty_context_chunks_returns_zero`).