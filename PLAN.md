# Solution plan

**Issue:** [Faithfulness checker crashes when a context chunk has `text: None` (#153)](https://github.com/ascherj/pathreview/issues/153)

### Understand

The `FaithfulnessChecker.check()` method scores how much of the generated feedback
is supported by the retrieved context chunks. To build the searchable context it
concatenates every chunk's text:

```python
context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])
```

**Root cause:** `dict.get("text", "")` returns its default (`""`) only when the key
is *absent*. When a chunk is `{"text": None}` — the key is present but the value is
`None` — `.get()` returns `None`. `str.join` requires every element to be a string,
so joining a list containing `None` raises
`TypeError: sequence item 0: expected str instance, NoneType found`.

- **Expected:** a `None` (or otherwise non-string) text value is treated like empty
  text; scoring proceeds and returns a float in `[0.0, 1.0]`.
- **Actual:** the entire faithfulness check crashes for any review whose retrieval
  yields a chunk with a null `text` field.

Confirmed by reproduction (Week 8): `test_none_context_chunk_text` fails with the
above `TypeError`, while `test_missing_text_key_in_chunk` passes — isolating the
defect to the explicit-`None` case.

### Map

Files/functions involved:

- **`rag/evaluator/faithfulness_checker.py`** — `FaithfulnessChecker.check()`, the
  list comprehension at lines 34–36. **This is the only file I expect to change.**
- **`tests/unit/test_faithfulness_checker.py`** — already contains the failing
  `test_none_context_chunk_text` and the passing `test_missing_text_key_in_chunk`;
  I may add one test for the "mixed null + valid chunks" case to lock in behavior.

No caller changes are needed — the fix is internal to `check()`; callers already
pass a `list[dict]` and consume a float.

### Plan

1. **Guard the text extraction.** Replace `chunk.get("text", "")` with logic that
   coerces a missing/`None`/non-string value to `""` before joining — e.g. build the
   list with `text = chunk.get("text") or ""` (or an explicit `isinstance(x, str)`
   check) so `None` never reaches `str.join`.
2. **Preserve valid chunks in mixed input.** Ensure non-null chunks in the same list
   still contribute their text (don't discard the whole list on one bad chunk).
3. **Verify the target tests pass.** Run `test_none_context_chunk_text` and
   `test_missing_text_key_in_chunk`, then the full `test_faithfulness_checker.py` file
   to confirm no regressions in the existing scoring tests.
4. **Strengthen coverage (optional).** Add a test with a mix of `{"text": None}` and a
   valid chunk, asserting the valid chunk's keywords still drive the score.
5. **Run project checks.** `make check` (ruff + black + mypy) and `make test-unit` so
   the change satisfies style, typing, and the wider suite.

### Inputs & outputs

- **Input:** `feedback: str` and `context_chunks: list[dict]`, where a chunk's
  `"text"` may be a normal string, missing, `None`, or (defensively) a non-string.
- **Output:** a `float` faithfulness score in `[0.0, 1.0]`. No exception is raised for
  null/missing text; such a chunk contributes empty text (i.e. no keywords) rather
  than crashing the run.

### Risks & unknowns

- **Coerce vs. drop:** two valid strategies (`None → ""` vs. filtering the chunk out).
  Both keep scoring alive and satisfy `test_none_context_chunk_text`; I'm leaning
  toward coercion so partially-null chunk sets still contribute. Low risk, but worth a
  note in the PR.
- **Broader non-string inputs:** the issue only names `None`, but the same `join` would
  break on any non-string (`int`, `dict`, ...). I'll guard defensively but keep the
  change minimal and scoped to the reported bug.
- **Type checking:** `context_chunks` is typed `list[dict]`; mypy may flag the new
  guard depending on inferred value types. I'll confirm `make typecheck` stays green.
- **Environment:** my local reproduction ran in a minimal venv under Python 3.14; the
  project targets 3.11. I need to run the full `make check`/`make test-unit` in the
  real project environment (Docker + venv) before finalizing, in case a pinned dep
  behaves differently.

### Edge cases

- `{"text": None}` → treated as `""` (the reported crash) — must not raise.
- Missing `"text"` key (`{"content": "..."}`) → `""` (already works; keep it working).
- `{"text": 123}` or other non-string → coerced/ignored without raising.
- **Mixed list**, e.g. `[{"text": None}, {"text": "Python expertise"}]` → the valid
  chunk still contributes to the score.
- **All chunks null**, e.g. `[{"text": None}, {"text": None}]` → context is effectively
  empty; claims come back unsupported (low score), not a crash.
- Empty feedback / empty `context_chunks` → unchanged early-return of `0.0`.
