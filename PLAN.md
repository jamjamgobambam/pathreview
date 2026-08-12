# Solution plan

**Issue:** [#153 — Faithfulness checker crashes when a context chunk has `text: None`](https://github.com/ascherj/pathreview/issues/153)

**Branch:** `fix/153-faithfulness-none-context-text`

## Understand

**Root cause.** `FaithfulnessChecker.check()` in `rag/evaluator/faithfulness_checker.py`
builds its context string at lines 34-36:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

`dict.get(key, default)` returns the default **only when the key is absent**. A
chunk that carries the key with an explicit `None` value — `{"text": None}` —
returns `None`, not `""`. `str.join` requires every item to be a `str` and
raises on the first `None` it meets.

**Expected behavior.** A chunk with null text contributes nothing to the
context, and `check()` returns a normal `float` score in `0.0-1.0` for whatever
remaining chunks do have text.

**Actual behavior.** The whole call raises
`TypeError: sequence item 0: expected str instance, NoneType found`, so no
score is produced at all. Reproduced locally and documented in `JOURNAL.md`
under "Reproduction (Week 8)".

**Why this input is realistic.** `rag/retriever/hybrid.py:126` copies ChromaDB
`documents` values straight into the `text` field with no coercion, so a
stored-but-empty document (an empty or failed extraction upstream in
`ingestion/`) propagates a null into exactly the chunk dicts the evaluator
consumes. This is not a synthetic input.

## Map

Files I expect to touch:

| File | Change |
|---|---|
| `rag/evaluator/faithfulness_checker.py` | **The fix.** Coerce null/missing text to `""` in `check()`, lines 34-36. |
| `tests/unit/test_faithfulness_checker.py` | Add regression tests for the edge cases below. `test_none_context_chunk_text` (line 231) already exists and must flip to passing. |
| `JOURNAL.md` | Week 8 entry; already holds the reproduction note. |
| `PLAN.md` | This file; updated as understanding evolves in Week 9. |

Files I have read and expect **not** to change, but which are part of the story:

- `rag/evaluator/eval_suite.py:28` — `EvalSuite.run()`, the real caller. Invokes
  `RelevanceScorer.score()` (line 40) then `FaithfulnessChecker.check()` (line 43).
- `rag/evaluator/relevance_scorer.py:32` — identical `.get("text", "")` pattern,
  crashes earlier on the same input. See Risks.
- `rag/generator/review_generator.py:157` — same pattern, does not crash but
  renders the literal string `"None"` into the LLM prompt.
- `rag/retriever/keyword_search.py:25` — uses `chunk["text"]` by direct index,
  so it would raise `KeyError` on a chunk with no `text` key at all.
- `rag/retriever/hybrid.py:126` — the upstream source of the null.

## Plan

1. **Fix the coercion in `check()`.** In `rag/evaluator/faithfulness_checker.py`,
   replace `chunk.get("text", "")` with a form that treats a present-but-null
   value the same as an absent key. Planned change:

   ```python
   context_text = " ".join([
       chunk.get("text") or "" for chunk in context_chunks
   ])
   ```

   `x or ""` maps `None`, `""`, and other falsy values to `""` in one step. The
   alternative, `str(chunk.get("text") or "")`, additionally survives non-string
   truthy values such as `42` or a list; I will decide between them in sub-task 2
   based on whether any caller can actually produce a non-string, and record the
   reasoning in a comment.

2. **Confirm the fix's blast radius by checking what the retriever can emit.**
   Read `rag/retriever/hybrid.py` and `rag/retriever/vector_store.py:106` to
   establish whether `text` can ever be a non-`str`, non-`None` value. If it
   cannot, keep the minimal `or ""` and do not add speculative `str()` coercion.

3. **Add regression tests** to `tests/unit/test_faithfulness_checker.py`
   covering the edge cases listed below — in particular the mixed-chunk case,
   which the existing single-chunk `test_none_context_chunk_text` does not
   exercise. CONTRIBUTING.md requires that every code change include or update
   relevant tests.

4. **Verify against the recorded baseline.** Run
   `python -m pytest tests/unit/test_faithfulness_checker.py`. The pre-fix
   baseline is **4 failed, 18 passed**; a correct fix must reach **3 failed,
   19 passed** plus my new tests. The three remaining failures are pre-existing
   scoring-threshold assertions unrelated to #153 (see Risks). Then run
   `make check && make test-unit` as CONTRIBUTING.md requires before a PR.

5. **Open the PR and file the sibling finding separately.** Use the
   `.github/PULL_REQUEST_TEMPLATE.md`, a `fix(rag):` Conventional Commit per
   CONTRIBUTING.md, and a `Fixes #153` footer. Report the `RelevanceScorer`
   crash (Risk 1) as its own issue rather than folding it into this PR.

## Inputs & outputs

**Signature is unchanged:**
`FaithfulnessChecker.check(self, feedback: str, context_chunks: list[dict]) -> float`.
No API, schema, or cross-module change; no caller needs updating.

**Input.** `context_chunks`, a `list[dict]` from the retriever. Each dict may
have a `text` key whose value is a `str`, `None`, or absent entirely. The fix
widens the accepted value domain to include `None`.

**Output.** A `float` in `0.0-1.0`. The behavioral change is narrow: inputs that
previously raised `TypeError` now return a score. Chunks with null text
contribute no tokens to `context_text`, so they neither support nor refute a
claim — they are simply skipped.

**What must not change:** every currently-passing test in
`tests/unit/test_faithfulness_checker.py` keeps passing, with identical scores
for all-`str` inputs. `test_score_consistency` (line 257) pins determinism and
`test_score_never_returns_hardcoded_value` (line 154) pins that scores still
vary with input.

## Risks & unknowns

1. **A sibling module crashes first on the same input, so the pipeline stays
   broken end-to-end.** I verified this: calling
   `EvalSuite().run("python skills", [{"text": None}], "Has Python skills")`
   raises `AttributeError: 'NoneType' object has no attribute 'lower'` from
   `rag/evaluator/relevance_scorer.py:32`, which runs at `eval_suite.py:40`,
   *before* the faithfulness check on line 43. Issue #153 and its named test are
   scoped to the faithfulness checker only. **Decision:** fix as specified,
   verify the sibling crash in a comment on the issue, and file it separately
   rather than silently widening the PR. Risk if I am wrong: a reviewer asks for
   both in one PR, which is a cheap change to make later.

2. **Three unrelated tests in the target file already fail**, so "all green" is
   not the success signal. `test_partial_support_returns_middle_score`,
   `test_multiple_context_chunks`, and `test_multiple_claims_varying_support`
   fail on the recorded baseline for reasons unrelated to null handling. I
   traced each: `_extract_claims` splits on sentences only, so it yields **one**
   claim for the first two tests, forcing the score to exactly `0.0` or `1.0`
   and never into an asserted middle band; separately, `_is_supported` tokenizes
   with a bare `.split()`, so `"Python,"` never matches `"Python"` and
   `test_multiple_context_chunks` scores `0.0` on an empty token overlap; and
   its `>= 2` meaningful-token threshold sinks both claims in
   `test_multiple_claims_varying_support`. All three are scoring-quality
   defects in `_extract_claims` and `_is_supported`, untouched by my fix. Risk:
   I mistake these for regressions from my own change, or "fix" them and blow
   the scope of a Tier 1 issue. Mitigation: the 4→3 failure count is written
   into `JOURNAL.md` before I touch any code.

3. **Unknown — which layer the maintainer wants the guard in.** Fixing the
   evaluator treats the symptom; normalizing at `rag/retriever/hybrid.py:126`,
   where the null enters, would fix every consumer at once. The issue text asks
   for the evaluator fix, so that is what I will do, but I will ask on the issue
   thread whether a retriever-level guard is preferred. Investigation path: read
   `hybrid.py:60-104` to see whether `text` is normalized anywhere before the
   blend, and check `git log` on that file for prior null-handling decisions.

4. **`or ""` also collapses non-empty falsy values.** For a keyword-overlap
   scorer, `0`, `False`, and `""` all contribute no meaningful tokens, so
   collapsing them is semantically correct here — but it is a silent behavior
   choice worth a comment so a future reader does not read it as a bug.

5. **Unknown — whether `scripts/run_evals.py` exercises this path.** Its
   docstring mentions scoring faithfulness (line 10), but I have not traced
   whether `make eval` reaches `check()` with live retriever output. If it does,
   it is a second, non-pytest way to demonstrate the fix.

## Edge cases

The fix must handle each of these without raising, returning a `float` in
`0.0-1.0` every time:

1. **`[{"text": None}]`** — the reported case. Context is empty, no claim finds
   support, so the expected result is `0.0`, not a crash. Pinned by the existing
   `test_none_context_chunk_text`.
2. **`[{"text": None}, {"text": "Python and Django expertise"}]`** — mixed
   chunks. The null must be skipped *without* discarding the real chunk beside
   it; the score must match what the real chunk alone would produce. This is the
   case the existing test misses and the one most likely to catch a sloppy fix
   that bails out of the loop early.
3. **`[{"text": None}, {"text": None}]`** — every chunk null. `context_chunks`
   is truthy so the `not context_chunks` guard at line 22 does not fire; the
   result should be `0.0` from zero supported claims, and specifically not the
   `0.5` neutral default returned at line 31 for unextractable claims.
4. **`[{"content": "Python skills"}]`** — key absent entirely. Already passes
   via `test_missing_text_key_in_chunk` (line 244) and must keep passing; this
   is the regression guard proving I did not break the working path.
5. **`[{"text": ""}]` and `[{"text": "   "}]`** — empty and whitespace-only
   strings. Both should behave like the null case. Whitespace is harmless
   because `_is_supported` tokenizes with `.split()`, which discards it.
6. **`[{"text": 42}]`** — non-string truthy value. Decided in sub-task 2: either
   coerce with `str()` or document that the retriever contract guarantees
   `str | None`. Whichever I choose, the behavior must be deliberate rather than
   an accidental second `TypeError` in the same `join`.
