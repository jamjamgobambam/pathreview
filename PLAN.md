## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` — https://github.com/ascherj/pathreview/issues/153

### Understand

**Root cause.** In `FaithfulnessChecker.check()`, the context string is built with:

```python
context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])
```

`dict.get(key, default)` only falls back to the default when the key is **missing**. When the key is present with an explicit `None` value, `.get()` returns `None`, so the list handed to `" ".join(...)` contains a `NoneType` and the join raises.

**Expected vs. actual**
- Expected: a chunk with null/missing text contributes nothing to the context; the check completes and returns a float in `[0.0, 1.0]`.
- Actual: `TypeError: sequence item 0: expected str instance, NoneType found`, which propagates up through `EvalSuite.evaluate()` and aborts the whole evaluation run — including chunks that were perfectly valid.

**Confirmed reproduction** (reliable, 100% of runs):

```
$ .venv/Scripts/python -c "from rag.evaluator.faithfulness_checker import FaithfulnessChecker; \
    FaithfulnessChecker().check('Knows Python.', [{'text': None}])"
TypeError: sequence item 0: expected str instance, NoneType found
  at rag/evaluator/faithfulness_checker.py:43

$ .venv/Scripts/python -m pytest tests/unit/test_faithfulness_checker.py -k none_context
FAILED tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text
1 failed, 21 deselected
```

### Map

| File | Role |
| --- | --- |
| `rag/evaluator/faithfulness_checker.py` | **Fix site.** `check()`, line 43 — the `" ".join(...)` over `chunk.get("text", "")`. |
| `tests/unit/test_faithfulness_checker.py` | Already contains the failing `test_none_context_chunk_text`; add cases for the neighbouring shapes below. |
| `rag/evaluator/eval_suite.py` | **Read-only.** Caller (`EvalSuite.evaluate()` line 43) — confirms the crash takes down a full eval run. Verify no behaviour change. |
| `rag/evaluator/relevance_scorer.py` | **Audit only.** Confirmed it uses the same `chunk.get("text", "")` idiom at line 32, so it is exposed to the same null chunk. Out of scope for #153 — I'll note it in the PR rather than widen the change. |

Expected to touch: `rag/evaluator/faithfulness_checker.py` and `tests/unit/test_faithfulness_checker.py`.

### Plan

1. **Lock in the reproduction.** Commit the annotated bug site (done) so the failing line and the failing test are documented in the branch history.
2. **Make context assembly null-safe.** Replace the comprehension with one that coerces non-string values away rather than trusting `.get()`'s default — filter out falsy/non-`str` values before joining, so `None`, missing keys, and non-string types (ints, dicts) all degrade to "contributes nothing".
3. **Handle the all-empty case.** If every chunk yields empty text, `context_text` is `""` and every claim scores unsupported → `0.0`. That is the correct, non-crashing answer; add an explicit log (`faithfulness_empty_context`) so an eval run that silently scores 0 is diagnosable rather than mysterious.
4. **Extend the tests.** Keep `test_none_context_chunk_text` as the regression test and add: all-chunks-`None`, mixed valid + `None` (the valid chunk must still score), and a non-string `text` value.
5. **Verify end to end.** Run the full `tests/unit/test_faithfulness_checker.py` suite plus `eval_suite`-touching tests, and re-run the one-liner repro to confirm it now returns a float. Run the repo lint/typecheck target (`make lint` / `make typecheck`) before opening the PR.

### Inputs & outputs

- **Input:** `feedback: str` and `context_chunks: list[dict]`, where any chunk's `"text"` may be missing, `None`, or a non-string.
- **Output:** a `float` in `[0.0, 1.0]` in every case — no exception. Chunks with usable text score exactly as they do today; unusable chunks contribute the empty string.
- **Changed:** the context-assembly expression inside `check()`, plus one new log line. No signature, return type, or scoring-formula change.

### Risks & unknowns

- **Silent degradation.** Skipping null chunks turns a loud crash into a quietly lower score. Mitigated by logging when context ends up empty — but a caller that *wants* to know its data is malformed won't see an exception. I believe non-crashing is the right call for an evaluator (the issue asks for it explicitly), but it's worth flagging in the PR.
- **Scoring drift.** If chunks currently rely on `.get("text", "")` producing `""` for missing keys, my change must preserve that exact behaviour — the existing `test_missing_text_key_in_chunk` guards this.
- **Unknown:** whether `None` text is itself a symptom of an upstream ingestion/chunker bug. Out of scope for this fix, but I'll check where chunks are constructed and note it in the PR rather than expanding the change.
- **Known, deferred:** `relevance_scorer.py:32` shares the exact idiom, so the same crash is one bad chunk away there too. Fixing it is a separate change; expanding this PR would blur the scope of #153.

### Edge cases

- `{"text": None}` — the reported case.
- Every chunk `None`/empty → return `0.0` without crashing.
- Mixed `[{"text": None}, {"text": "Python expertise"}]` → the valid chunk still counts; score must not be dragged to 0.
- Missing key entirely, `{"content": ...}` (wrong key) → unchanged, empty contribution.
- Non-string `text` (int, list, dict) → treated as no text, not stringified into garbage tokens.
- `{"text": ""}` and whitespace-only text → no tokens, no crash.
- `context_chunks=[]` or falsy `feedback` → already short-circuits to `0.0` at the top of `check()`; unchanged.
