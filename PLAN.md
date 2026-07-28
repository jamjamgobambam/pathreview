# PLAN.md — Issue #153: Faithfulness checker crashes on `text: None`

**Issue:** https://github.com/ascherj/pathreview/issues/153
**Branch:** `fix/153-faithfulness-checker-null-chunk-text`
**Pull Request:** https://github.com/ascherj/pathreview/pull/339 (open)

## Problem

`FaithfulnessChecker.check()` builds its context string with:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

`dict.get(key, default)` only substitutes the default when the key is **missing**. If a chunk is `{"text": None}` (key present, value `None`), `.get()` returns `None`, and `str.join` raises:

```
TypeError: sequence item 0: expected str instance, NoneType found
```

This can happen whenever an upstream retriever or DB row produces a chunk with a null/empty text field, crashing the whole evaluation pipeline instead of just scoring that chunk as unsupported.

## a) Files to modify or create

| File | Change |
|---|---|
| `rag/evaluator/faithfulness_checker.py` | **Modify.** Fix the `.get()` call in `check()` (line 34-36) so a `None` value falls back to `""` the same way a missing key already does. |
| `tests/unit/test_faithfulness_checker.py` | **Modify (minor).** `test_none_context_chunk_text` and `test_missing_text_key_in_chunk` already exist and cover this exact case — no new tests are strictly required. Optionally add one case mixing a valid chunk with a `None`-text chunk in the same list, to confirm partial data doesn't get dropped. |
| `JOURNAL.md` | **Modify.** Week 8 entry documenting reproduction (already added). |
| No changes needed to `rag/evaluator/eval_suite.py` | Confirmed its only interaction is calling `self.faithfulness_checker.check(feedback, chunks)` — it passes through whatever chunks it receives, so the fix at the source is sufficient. |

## b) Ordered sub-tasks

1. **Reproduce (done)** — confirmed `TypeError` locally via the exact snippet in the issue, and via `pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text`.
2. **Fix the list comprehension** in `FaithfulnessChecker.check()`:
   ```python
   context_text = " ".join([
       chunk.get("text") or "" for chunk in context_chunks
   ])
   ```
   `chunk.get("text")` returns `None` for both a missing key and an explicit `None` value; `or ""` normalizes both to an empty string, matching the already-passing `test_missing_text_key_in_chunk` behavior.
3. **Run the targeted test** to confirm `test_none_context_chunk_text` passes:
   ```
   pytest tests/unit/test_faithfulness_checker.py -k none_context_chunk_text -v
   ```
4. **Run the full unit suite** for this file and note the three pre-existing unrelated failures (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, `test_multiple_claims_varying_support`) are untouched by this change — confirming no new regressions and no accidental scope creep into the scoring-threshold behavior.
5. **Run the whole unit suite** (`make test-unit`) to confirm no other module depends on the old crash-on-`None` behavior.
6. **Run `make check`** (ruff + black + mypy) to satisfy the repo's contribution checklist.
7. **Update JOURNAL.md / PLAN.md** if the implementation deviates from this plan.
8. **Commit** using Conventional Commits, e.g.:
   ```
   fix(rag): handle None chunk text in faithfulness checker

   FaithfulnessChecker.check() used chunk.get("text", "") to build the
   context string, but .get()'s default only applies to a missing key —
   a chunk with an explicit `text: None` still returned None and crashed
   " ".join(...) with a TypeError. Normalize None to "" the same way a
   missing key is already handled.

   Fixes #153
   ```
9. **Open a PR** against `ascherj/pathreview` using the repo's PR template, linking `Closes #153`.

## c) Edge cases, risks, and side effects

- **Empty string vs. `None` vs. missing key** — all three now collapse to the same "no text contribution" behavior. This matches the existing passing test for a missing key, so behavior stays consistent rather than introducing a third code path.
- **Mixed chunk lists** (some valid, some `None`) — a `None` chunk should contribute nothing to `context_text` but must not blank out the *other* valid chunks in the same list. The one-line fix preserves this since each chunk is mapped independently before `join`.
- **Same bug pattern exists elsewhere** — `chunk.get("text", "")` (same footgun) also appears in:
  - `rag/evaluator/relevance_scorer.py:32`
  - `rag/generator/review_generator.py:157`
  - `rag/retriever/hybrid.py:85`
  These are **out of scope for #153** (issue is scoped to the faithfulness checker only) but are worth flagging separately — a follow-up issue may be warranted so they don't crash the same way in production. Do not touch these files in this PR to keep the diff focused and reviewable.
- **Falsy-but-valid text values** — `or ""` treats any falsy value (`None`, `""`, `0`, `False`) as empty. `text` is expected to always be a string or `None` per the data model, so `0`/`False` aren't realistic inputs here; if that assumption changes later, prefer an explicit `is None` check instead of `or`.
- **No behavior change for the "happy path"** — chunks with real string text are unaffected; only the null/missing-key fallback path changes.
- **Downstream consumers** — `eval_suite.py` only reads the returned float score; no shape/type change to worry about there.
- **Pre-existing unrelated test failures** — `test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, and `test_multiple_claims_varying_support` fail on `main` before this change (scoring-threshold issues in `_is_supported`, unrelated to `None` handling). Leave them alone; fixing them is outside this issue's scope and would inflate the PR's diff and review surface.
