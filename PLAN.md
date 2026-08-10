## Solution plan

**Issue:** [#153 — Faithfulness checker crashes when a context chunk has `text: None`](https://github.com/ascherj/pathreview/issues/153)

### Understand

**Root cause:** In `rag/evaluator/faithfulness_checker.py`, the `check()` method builds a
context string by joining chunk text values:

```python
context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])
```

`dict.get("text", "")` returns `""` only when the `"text"` key is **missing** from the
chunk dict. When the key is present but its value is `None` (e.g. `{"text": None}`),
`.get()` returns `None`, not `""`. Passing `None` into `" ".join(...)` raises:

```
TypeError: sequence item 0: expected str instance, NoneType found
```

**Expected behavior:** The faithfulness checker should treat a `None` text value the same
as an empty string — gracefully producing a score (0.0 in this case, since no context is
available) instead of crashing.

**Actual behavior (before fix):** `TypeError` crash, halting the entire RAG evaluation
pipeline whenever any retrieved chunk has a null `text` field.

### Map

**Files involved:**

- `rag/evaluator/faithfulness_checker.py` — **primary fix target**, line 38 (the
  `context_text` join expression in `check()`).
- `tests/unit/test_faithfulness_checker.py` — contains the regression tests
  `test_none_context_chunk_text` (line 231) and `test_missing_text_key_in_chunk`
  (line 244) that verify the fix.
- `reproduce_issue_153.py` — reproduction script demonstrating the original bug and
  the fix (added in Week 8).

**Functions/modules:**

- `FaithfulnessChecker.check()` — the method where the join happens.
- `FaithfulnessChecker._extract_claims()` and `_is_supported()` — downstream methods
  that consume `context_text`; they are not directly affected but benefit from the
  guaranteed string input.

### Plan

The fix has already been applied in Week 7 (commit `c7ae749`). The remaining sub-tasks
for Week 8–9 are verification and documentation:

1. **Reproduce the bug** — Create `reproduce_issue_153.py` that simulates the original
   buggy `.get("text", "")` expression and confirms the `TypeError`, then runs the fixed
   `check()` method to show it returns a valid score. *(Done — committed as `3fdf3b9`)*

2. **Verify the fix with tests** — Run the targeted unit tests
   `test_none_context_chunk_text` and `test_missing_text_key_in_chunk` to confirm they
   pass with the fix in place. Also run the full test suite to check for regressions.
   *(Done — both tests pass; 3 pre-existing failures are unrelated to this issue.)*

3. **Run linting and type checks** — Ensure `ruff`, `black`, and `mypy` pass on the
   modified file and the reproduction script. *(Done — pre-commit hooks pass.)*

4. **Open a pull request** — Push the branch and open a PR against the upstream repo
   with a description referencing issue #153, the reproduction steps, and the fix.
   *(Week 9 task.)*

5. **Address PR feedback** — Respond to reviewer comments, adjust code if needed, and
   get the PR merged. *(Week 9 task.)*

### Inputs & outputs

**Input:** A list of context chunk dicts, where one or more chunks may have:
- `{"text": None}` — key present, value is `None`
- `{}` or `{"content": "..."}` — `"text"` key missing entirely

**Output:** A `float` faithfulness score in `[0.0, 1.0]`. When all chunk text values are
`None` or missing, the context string is `""`, no claims are supported, and the score is
`0.0` — no crash.

**Fix expression (before → after):**

```python
# Before (buggy):
context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])

# After (fixed):
context_text = " ".join([chunk.get("text") or "" for chunk in context_chunks])
```

The `or ""` idiom coerces both `None` and missing-key (which `.get("text")` returns as
`None`) to an empty string.

### Risks & unknowns

- **Pre-existing test failures:** Three tests (`test_partial_support_returns_middle_score`,
  `test_multiple_context_chunks`, `test_multiple_claims_varying_support`) fail due to
  the stop-word filtering logic in `_is_supported()`, not because of this fix. These are
  separate issues and should not block the PR for #153.
- **Upstream merge conflicts:** The upstream repo may have changes to
  `faithfulness_checker.py` since the fork. Need to rebase before opening the PR.
- **Chunk text as non-string types:** The fix handles `None` but not, e.g., integers or
  lists. The issue scope is limited to `None`; other type coercion is out of scope.

### Edge cases

- **`{"text": None}`** — key present, value `None` → coerced to `""` ✓
- **`{}` (missing key)** — `.get("text")` returns `None` → coerced to `""` ✓
- **`{"text": ""}`** — empty string → stays `""` ✓
- **Mixed chunks:** `[{"text": "Python skills"}, {"text": None}, {"content": "x"}]` →
  joins to `"Python skills  "` (extra spaces are harmless for token overlap) ✓
- **All chunks are `None`/missing** — context is `""`, all claims unsupported, score `0.0` ✓
- **`context_chunks` is `None`** — handled by the early `if not context_chunks` guard
  on line 23 (returns `0.0`) ✓
