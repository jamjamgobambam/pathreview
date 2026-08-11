## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` —
https://github.com/ascherj/pathreview/issues/153

### Understand

**Root cause.** In `FaithfulnessChecker.check()`, the context string is built
with `chunk.get("text", "")`. The `""` default is only used when the `"text"`
key is *absent*. When a chunk carries the key with a `None` value
(`{"text": None}`), `.get()` returns `None`, and the subsequent
`" ".join([...])` raises `TypeError: sequence item 0: expected str instance,
NoneType found`.

**Expected vs. actual.**
- *Expected:* a null-text chunk is treated as empty context and contributes
  nothing; `check()` still returns a valid `float` in `[0.0, 1.0]` computed from
  the remaining (valid) chunks.
- *Actual:* the whole call raises `TypeError` and no score is returned. A single
  malformed chunk anywhere in the retrieved set aborts the entire faithfulness
  evaluation.

Reproduced locally (Week 8):
```
FaithfulnessChecker().check("Knows Python.", [{"text": None}])
# TypeError: sequence item 0: expected str instance, NoneType found
# (rag/evaluator/faithfulness_checker.py:34)
```
The existing unit test `test_none_context_chunk_text` fails with this same
traceback.

### Map

Files/functions involved:

- `rag/evaluator/faithfulness_checker.py` — **the file I will fix.** Specifically
  the list comprehension inside `FaithfulnessChecker.check()` (~lines 34–36, now
  annotated with a `BUG #153` comment) that builds `context_text`.
- `tests/unit/test_faithfulness_checker.py` — **the file I will verify against.**
  Already contains `test_none_context_chunk_text` (line 231) and the related
  `test_missing_text_key_in_chunk` (line 244). I will make sure both pass and may
  add an explicit assertion that a mix of valid + `None` chunks still scores.

No other modules, API routes, DB models, or frontend code are involved.

### Plan

1. **Coerce non-string chunk text to `""`.** Replace `chunk.get("text", "")`
   with a form that guards against `None` (and any non-`str`), e.g.
   `str(chunk.get("text") or "")` or an explicit helper that returns `""` when
   the value is falsy/`None`. Keep it a one-line, minimal change in `check()`.
2. **Remove/replace the `BUG #153` reproduction comment** with a short comment
   explaining *why* the coercion is needed (so the guard isn't "simplified" away
   later).
3. **Run the targeted tests** — `test_none_context_chunk_text` and
   `test_missing_text_key_in_chunk` — and confirm both pass and return a float in
   `[0.0, 1.0]`.
4. **Run the full module suite** (`pytest tests/unit/test_faithfulness_checker.py`)
   to confirm no regression in the already-passing tests, and re-run
   `make check` (ruff/black/mypy) for style/type compliance.
5. **Open a PR** referencing `Fixes #153`, following the conventional-commit and
   PR-template conventions in `docs/CONTRIBUTING.md`.

### Inputs & outputs

- **Input:** `check(feedback: str, context_chunks: list[dict])`, where any chunk
  may have `text` missing, `None`, or a non-string value.
- **Output:** a `float` faithfulness score in `[0.0, 1.0]`. `None`/missing text
  is treated as an empty contribution; the score is computed from valid chunks.
  No exception is raised for malformed chunk text.
- **Changed behavior:** only the `context_text` construction becomes
  null-safe. Scoring math, claim extraction, and the empty-input short-circuit
  are untouched.

### Risks & unknowns

- **Scope creep into #152.** Running the suite shows three *other* failing tests
  (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
  `test_multiple_claims_varying_support`). These are scoring-threshold failures
  that belong to a separate issue (#152, "faithfulness checker can never mark
  short claims as supported"), **not** #153. Risk: accidentally "fixing" scoring
  logic here. Mitigation: my change touches only `None`-coercion in the join;
  those three tests are expected to remain failing after my fix and are out of
  scope.
- **Prior art / duplicate work — PR #211 (checked Week 8).** An open, unmerged,
  unreviewed PR by another contributor (ahmedtaha100) is titled
  `fix(rag): support short claims in faithfulness checker` and declares both
  `Closes #153` and `Closes #152`. It fixes my crash as a side effect of a larger
  rewrite: it replaces the `" ".join(chunk.get("text", ""))` line with a guarded
  tokenizer loop —
  `chunk_text = chunk.get("text"); if isinstance(chunk_text, str): context_tokens |= self._tokenize(chunk_text)`.
  Decision: I'm keeping my focused, minimal fix for #153 (null-coercion only, no
  scoring changes). Rationale: #211 bundles two issues and rewrites scoring
  (#152 territory), which a maintainer may ask to split; my change is narrower and
  independently reviewable. If I open an upstream PR I will reference #211 and
  argue for the scoped fix. My branch/grade does not depend on #211's outcome.
- **Overly broad coercion.** Using `str(x)` on a non-`None`, non-`str` value
  (e.g. an int) would stringify it rather than drop it. Unknown whether chunks
  ever legitimately carry non-string text; I'll prefer coercing only `None`/falsy
  to `""` to stay conservative and match the test's intent.
- **Type signature.** `context_chunks` is typed `list[dict]`; mypy under
  `make check` may flag the coercion depending on inferred value types. I'll
  confirm the typecheck passes.

### Edge cases

- `{"text": None}` — the reported crash; must yield `""` contribution.
- `{"content": "..."}` — `text` key entirely missing (covered by
  `test_missing_text_key_in_chunk`); must yield `""`.
- Mixed list, e.g. `[{"text": "Python expertise"}, {"text": None}]` — must not
  crash and must still score using the valid chunk.
- All chunks null/empty (`[{"text": None}, {"text": None}]`) — should behave like
  empty context (no claims supported), returning a valid float, not an error.
- Whitespace/empty-string text (`{"text": ""}`) — already handled; must continue
  to work.
- Non-string, non-None text (e.g. `{"text": 123}`) — decide and document: coerce
  or drop; must not raise.
