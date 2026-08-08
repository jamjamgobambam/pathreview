## Solution plan

**Issue:** #153 - Faithfulness checker crashes when a context chunk has `text: None` - https://github.com/ascherj/pathreview/issues/153

### Understand
**Root cause:** In `FaithfulnessChecker.check()`, the context string is built with
`chunk.get("text", "")`. Python's `dict.get(key, default)` only returns `default`
when the key is *absent*. When the `"text"` key is present but its value is `None`,
`.get()` returns `None`. The next statement, `" ".join([...])`, requires every item
to be a `str`, so a `None` raises `TypeError: sequence item 0: expected str instance,
NoneType found` (`faithfulness_checker.py:34`).

**Expected:** A chunk with `text: None` is treated like empty/missing text; `check()`
returns a valid `float` in `[0.0, 1.0]`.

**Actual:** The entire faithfulness evaluation crashes. One malformed chunk takes down
scoring for the whole response.

### Map
- `rag/evaluator/faithfulness_checker.py` - the `check()` method, ~line 34 (context
  concatenation). This is the only file that needs a code change.
- `tests/unit/test_faithfulness_checker.py` - already contains `test_none_context_chunk_text`
  (the target, currently failing) and `test_missing_text_key_in_chunk` (related, currently
  passing - guards the missing-key path). No new test is required; the target test already
  encodes acceptance.

### Plan
1. **Reproduce & pin** (Week 8, done): run `test_none_context_chunk_text`, confirm the
   `TypeError` at line 34, record the traceback in JOURNAL.md.
2. **Fix the concatenation**: change the comprehension to `chunk.get("text") or ""`, which
   coerces missing key, `None`, and empty string to `""` uniformly.
3. **Verify the guards**: run `test_none_context_chunk_text` and `test_missing_text_key_in_chunk`
   - both must pass.
4. **Check for regressions**: run the full `test_faithfulness_checker.py` file and confirm no
   previously-passing test breaks. The 3 pre-existing scoring-threshold failures are OUT OF
   SCOPE and must remain unchanged - not "fixed."
5. **Ship**: commit on `fix/153-faithfulness-none-context-chunk`, update JOURNAL/PLAN, open a
   PR that references #153 with a one-line rationale for the fix choice.

### Inputs & outputs
**Input:** `check(feedback: str, context_chunks: list[dict])`, where one or more chunks may
have `text` set to `None` or omit the key entirely.
**Output:** a `float` faithfulness score in `[0.0, 1.0]`, no exception. A `None`/missing text
contributes an empty string to the concatenated context (i.e., contributes nothing), matching
how a genuinely empty chunk already behaves.

### Risks & unknowns
- **Scope trap (main risk):** `make test-unit` is NOT fully green on `main`.
  `test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, and
  `test_multiple_claims_varying_support` already fail because `_is_supported` requires >=2
  meaningful-token overlap and those fixtures share only 1. They are unrelated to #153. The
  risk is scope creep - touching `_is_supported` or the threshold to chase a "fully green"
  suite. Acceptance for this issue is `test_none_context_chunk_text` alone.
- **Semantic choice:** `chunk.get("text") or ""` also collapses other falsy values (`0`,
  `False`) to `""`. For a text field that is acceptable, but I'll note the strict alternative
  in the PR in case a reviewer prefers None-only handling.
- **Unknown:** whether other call sites in `rag/` read `chunk["text"]` directly and could hit
  the same `None` problem. The issue scopes only the checker, so I'll flag but not chase this.

### Edge cases
- `{"text": None}` -> treated as empty (the target case).
- `{"content": "..."}` (missing `text` key) -> already handled; must stay handled.
- `{"text": ""}` (empty string) -> contributes nothing, no crash.
- Mixed list (some valid chunks, some `None`/missing) -> valid chunks still score; no crash.
- All chunks `None`/empty -> empty context -> `_is_supported` finds no overlap -> score `0.0`
  (a valid float, not a crash).
