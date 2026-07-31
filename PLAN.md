# PLAN

## Solution plan

**Issue:** [#153 — Faithfulness checker crashes when a context chunk has `text: None`](https://github.com/ascherj/pathreview/issues/153)

### Understand

**Root cause:** `FaithfulnessChecker.check()` builds its context string with
`chunk.get("text", "") for chunk in context_chunks` (`rag/evaluator/faithfulness_checker.py:39`).
`dict.get(key, default)` only returns `default` when `key` is *absent* from the
dict. If a chunk dict has the key present but explicitly set to `None` (e.g.
`{"text": None}`), `.get()` returns `None`, not `""`. The subsequent
`" ".join([...])` call then raises `TypeError: sequence item 0: expected str
instance, NoneType found` because `str.join` cannot join a `None` element.

**Expected behavior:** A chunk with `"text": None` should be treated the same
as an empty/missing chunk — contribute nothing to `context_text` — and
`check()` should return a valid float score (0.0–1.0), same as it does for a
chunk with a missing `"text"` key.

**Actual behavior:** `check()` raises an unhandled `TypeError` and crashes the
caller, instead of degrading gracefully.

**Confirmed via reproduction:** running
`tests/unit/test_faithfulness_checker.py::test_none_context_chunk_text`
reproduces the exact `TypeError` above (see reproduction commit `966b683`).

### Map

Files/functions involved:

- `rag/evaluator/faithfulness_checker.py` — `FaithfulnessChecker.check()`,
  specifically the list comprehension at line 39. This is the fix target
  named in the issue.
- `tests/unit/test_faithfulness_checker.py` — `test_none_context_chunk_text`
  (line 231) already exists and currently fails; it should pass once the fix
  lands. `test_missing_text_key_in_chunk` (line 244) already passes and must
  keep passing (it covers the *missing key* case, which `.get()` already
  handles correctly).
- Not in scope, but noted for awareness: the identical `chunk.get("text", "")`
  pattern also appears in `rag/generator/review_generator.py:157`,
  `rag/evaluator/relevance_scorer.py:32`, and `rag/retriever/hybrid.py:85`.
  None of these are named in issue #153, so I will not change them, but the
  same latent crash likely exists there too (see Risks below).

### Plan

1. In `rag/evaluator/faithfulness_checker.py`, change the context-text
   comprehension so a `None` value for `"text"` is coerced to `""` instead of
   passed through as-is, e.g. `chunk.get("text") or ""` (or
   `chunk.get("text", "") or ""`), so both "missing key" and "key present but
   None" resolve to an empty string.
2. Remove the now-redundant reproduction comment added at line 34-38 (or
   fold it into a short explanatory note) once the real fix is in, so the
   comment doesn't read as a leftover TODO.
3. Run `tests/unit/test_faithfulness_checker.py` and confirm
   `test_none_context_chunk_text` passes and all other tests in that file
   still pass (18 currently pass unrelated to this bug; 3 pre-existing
   unrelated failures — `test_partial_support_returns_middle_score`,
   `test_multiple_context_chunks`, `test_multiple_claims_varying_support` —
   are out of scope for #153, see Risks below).
4. Run the full unit suite (`make test-unit`) to confirm no regressions
   outside this file.
5. Update `JOURNAL.md` / open a PR referencing issue #153 with a summary of
   the fix and test evidence.

### Inputs & outputs

- **Input:** `context_chunks: list[dict]` passed into `check()`, where any
  chunk dict may have `"text"` missing, `"text": None`, or `"text": "<str>"`.
- **Output:** `check()` should always return a `float` in `[0.0, 1.0]` and
  never raise, regardless of which of the three `"text"` states above appears
  in any chunk — a `None`/missing chunk should behave as if it contributed no
  context text, not crash the whole scoring pass.

### Risks & unknowns

- **Scope creep:** The same bug pattern exists in `review_generator.py:157`,
  `relevance_scorer.py:32`, and `hybrid.py:85`. Issue #153 only names
  `faithfulness_checker.py`, so I'll keep the fix scoped there, but I'm unsure
  whether the reviewer wants a follow-up issue filed for the sibling cases or
  a proactive fix in the same PR. Will confirm before touching those files.
- **Unrelated pre-existing failures:** 3 other tests in
  `test_faithfulness_checker.py` fail today for reasons unrelated to `#153`
  (looks like a claim-extraction/overlap-scoring issue in `_extract_claims`/
  `_is_supported`, not the `None`-text bug). Need to confirm with a
  mentor/instructor whether these are a separate known issue or something I
  should also flag, so I don't conflate two bugs in one PR.
- **`or ""` vs explicit `is None` check:** Using `chunk.get("text") or ""`
  also coerces falsy-but-valid values (e.g. `""` itself, which is already
  fine) — need to double check there's no case where a chunk's `text` is a
  falsy non-string value (e.g. `0`) that should be preserved as-is. Given the
  field is always meant to be a string, this seems safe, but worth a second
  look during implementation.

### Edge cases

- Chunk dict missing the `"text"` key entirely (already handled, must keep
  passing — `test_missing_text_key_in_chunk`).
- Chunk dict with `"text": None` (the bug — must be fixed).
- Chunk dict with `"text": ""` (already works, must keep working).
- `context_chunks` containing a mix of valid text, `None`, and missing-key
  chunks in the same call (not currently tested — worth adding a test case).
- Empty `context_chunks` list (already handled via the early `if not
  context_chunks` guard at the top of `check()`).
