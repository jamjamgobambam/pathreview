## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` ([#153](https://github.com/ascherj/pathreview/issues/153))

### Understand
`FaithfulnessChecker.check()` builds the context string with
`chunk.get("text", "") for chunk in context_chunks`. The `.get(key, default)`
default only applies when `key` is **absent** from the dict — if `"text"` is
present but explicitly `None`, `.get()` returns `None`. That `None` then
lands in the list passed to `" ".join(...)`, and `str.join` requires every
item to be a `str`, so it raises:

```
TypeError: sequence item 0: expected str instance, NoneType found
```

- **Expected:** a chunk with `{"text": None}` should be treated like an empty
  or missing chunk — `check()` still returns a normal `float` in `[0.0, 1.0]`.
- **Actual:** the whole call crashes, taking down whatever caller invoked it
  (currently `EvalSuite.run()`), not just the one malformed chunk.

### Map
- `rag/evaluator/faithfulness_checker.py` — `check()`, the `context_text = " ".join(...)` line (~34-42). This is the only file the fix touches.
- `tests/unit/test_faithfulness_checker.py` — `test_none_context_chunk_text` (already present, currently failing) and `test_missing_text_key_in_chunk` (already passing) encode the expected behavior; no new test file needed, just make the failing one pass without breaking the passing one.
- `rag/evaluator/eval_suite.py` — the only current caller of `FaithfulnessChecker.check()` (via `EvalSuite.run()`); confirms the blast radius is a full eval run, not just one chunk.
- `rag/evaluator/relevance_scorer.py:32` — has the identical `chunk.get("text", "")` pattern. Out of scope for #153 (different file, different issue), but worth a quick look so I don't miss an obviously-related crash while I'm in this area.

### Plan
1. Replace `chunk.get("text", "")` with something that coerces `None` to `""` too (e.g. `chunk.get("text") or ""`), so both a missing key and an explicit `None` value fall back to an empty string.
2. Run `pytest tests/unit/test_faithfulness_checker.py -v` and confirm `test_none_context_chunk_text` now passes and every previously-passing test still passes (especially `test_missing_text_key_in_chunk`, to make sure the fix doesn't change that behavior).
3. Manually exercise `EvalSuite.run()` with a mixed `chunks` list (one chunk with real text, one with `"text": None`) to confirm the score reflects the real chunk instead of crashing or silently zeroing out.
4. Run the full unit suite (`pytest tests/unit/`) to check for regressions outside this file.
5. Update `JOURNAL.md` Week 8 (this entry) and open the PR against `fix/153-faithfulness-checker-none-context-text`, scoped only to `faithfulness_checker.py`.

### Inputs & outputs
- **Input:** `feedback: str`, `context_chunks: list[dict]`, where each dict may have `"text": str`, `"text": None`, or no `"text"` key at all.
- **Output:** unchanged — a `float` faithfulness score in `[0.0, 1.0]`. The only behavior change is that a `None`/missing `"text"` chunk contributes `""` to the joined context instead of crashing the whole check.

### Risks & unknowns
- Whether a `None`-text chunk should just be silently treated as empty (matching how a missing key is already handled) or should also log something so a broken upstream retriever is noticeable. Leaning toward silent + consistent with the missing-key path, since that's the existing precedent in this file.
- `relevance_scorer.py:32` has the same `.get("text", "")` gap and its `_tokenize()` isn't yet confirmed to be `None`-safe — a similar crash may still be reachable via `EvalSuite.run()` through the relevance path even after this fix lands. Flagging as a possible follow-up issue rather than folding it into #153.
- Haven't traced whether the retrievers (`hybrid.py`, `vector_store.py`) ever legitimately produce `text: None`, or whether this is purely a defensive fix for malformed/adversarial input. Doesn't change the fix, but affects whether this is worth a code comment upstream too.

### Edge cases
- `{"text": None}` — the reported crash.
- `{}` (no `"text"` key) — already handled today; must not regress.
- `{"text": ""}` — already handled today; must not regress.
- A `context_chunks` list mixing valid, `None`, and missing-key chunks together.
- Every chunk in the list has `None`/missing text — `context_text` ends up `""`, so every claim should be reported unsupported (score `0.0`), not a crash.
