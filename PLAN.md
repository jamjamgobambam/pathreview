## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` — https://github.com/ascherj/pathreview/issues/153

### Understand

The root cause is in `FaithfulnessChecker.check()`, specifically this line:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

`dict.get(key, default)` only returns `default` when `key` is **missing** from the dictionary — not when `key` is present but its value is explicitly `None`. When a context chunk looks like `{"text": None}`, `.get("text", "")` still returns `None`, and `" ".join([...])` then raises a `TypeError` because it can't join a `None` value with strings.

**Expected behavior:** the faithfulness checker should treat a chunk with `text: None` the same as a chunk with empty or missing text, and continue scoring gracefully.

**Actual behavior:** the whole `check()` call crashes with `TypeError: sequence item 0: expected str instance, NoneType found`, which would take down the entire review pipeline for any portfolio review that includes a chunk like this.

### Map

- `rag/evaluator/faithfulness_checker.py` — contains `FaithfulnessChecker.check()`, specifically the `context_text` concatenation step where the bug lives
- `tests/unit/test_faithfulness_checker.py` — contains `test_none_context_chunk_text`, the pre-written test that validates this exact fix, and `test_missing_text_key_in_chunk`, a related test for the "key missing entirely" case that must not regress

### Plan

1. Reproduce the crash locally using a minimal script (`reproduce_issue_153.py`) that calls `FaithfulnessChecker().check()` with a `{"text": None}` chunk and confirm the exact `TypeError` from the issue occurs
2. Identify the exact faulty line (`chunk.get("text", "")`) and confirm the root cause by reasoning through Python's `dict.get()` default behavior
3. Apply the fix by changing `chunk.get("text", "")` to `chunk.get("text") or ""`, which normalizes both "missing key" and "key present but None" to an empty string
4. Run the full test file (`tests/unit/test_faithfulness_checker.py`) and confirm `test_none_context_chunk_text` passes, and that `test_missing_text_key_in_chunk` still passes with no regression
5. Use `git stash` / `git stash pop` to isolate the effect of the fix — run the test suite with the fix removed to confirm the exact same failure reproduces, then restore the fix and confirm it resolves cleanly

### Inputs & outputs

- **Input:** `context_chunks: list[dict]`, where each dict may have `"text"` missing entirely, `"text": None`, or `"text": "<some string>"`
- **Output:** `check()` should always return a `float` between `0.0` and `1.0`, regardless of which of these three text states appears in any given chunk — it should never raise an exception due to chunk content

### Risks & unknowns

- **Risk:** silently converting `None` to an empty string could mask a real upstream data-quality issue. If `None` values are showing up frequently in `context_chunks`, that might indicate a bug further upstream in the ingestion pipeline (`ingestion/`) that's worth flagging separately — this fix treats the symptom safely, but doesn't investigate whether the root cause is elsewhere. Out of scope for this issue, but worth a follow-up note.
- **Confirmed pre-existing issue (not a risk introduced by this fix):** 3 tests in `test_faithfulness_checker.py` — `test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, and `test_multiple_claims_varying_support` — fail independently of this change. They appear related to a separate bug in `_is_supported()`'s stop-word filtering or the "≥2 meaningful tokens" overlap threshold. Confirmed via `git stash` isolation that these fail identically with and without my fix applied. Explicitly out of scope for #153.

### Edge cases

1. A single chunk with `{"text": None}` — must not crash, must return a valid float score
2. Multiple chunks in the same list, where some have `None` text and others have valid string text — must concatenate correctly using only the valid text, without crashing on the `None` entries
3. A chunk missing the `"text"` key entirely (e.g. `{"content": "..."}`) — this case worked correctly before the fix and must continue to work identically afterward (no regression), since `.get("text")` returns `None` for a missing key just as it does for an explicit `None` value