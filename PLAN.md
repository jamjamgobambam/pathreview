## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` — [Issue #153](https://github.com/ascherj/pathreview/issues/153)

### Understand

**Feature purpose.** `FaithfulnessChecker.check(feedback, context_chunks)` returns a
`0.0`–`1.0` score estimating how much of the generated feedback is *supported* by the
retrieved context. It splits the feedback into "claims" (sentences), concatenates all
context chunk texts into a single string, and counts the claims that share at least two
meaningful (non-stopword) tokens with that concatenated context. It is one of two scorers
aggregated by `EvalSuite.run()` into an overall evaluation score.

**Expected behavior.** Given any list of context chunks — including chunks whose `text`
value is `None` — `check()` should return a valid float in `[0.0, 1.0]` rather than raise an error.
A `None` (or empty) chunk should contribute no tokens to the context, while valid chunks continue to score.

**Actual behavior.** When a chunk is `{"text": None}`, `check()` raises:

```
TypeError: sequence item 0: expected str instance, NoneType found
```

at the `" ".join(...)` in `rag/evaluator/faithfulness_checker.py`.

**Confirmed root cause.** `{"text": None}.get("text", "")` returns `None`, **not** `""`.
`dict.get`'s default is used only when the key is *absent*, never when the key is present
with a `None` value. The `None` then flows into `" ".join([...])`, which requires every
sequence item to be a `str`, and the join raises `TypeError`. The sibling test
`test_missing_text_key_in_chunk` (`{"content": ...}`, `text` key absent) passes because the
`""` default *is* applied there — confirming the crash is specific to a present-but-`None`
value.

### Map

Relevant files, classes, functions, and execution path:

- **`rag/evaluator/faithfulness_checker.py`** — `class FaithfulnessChecker`, method
  `check()` ([faithfulness_checker.py:12](rag/evaluator/faithfulness_checker.py#)).
  This is the planned location of the source-code change. 
- **`rag/evaluator/eval_suite.py`** — `EvalSuite.run()` calls
  `self.faithfulness_checker.check(feedback, chunks)` at
  [eval_suite.py:43](rag/evaluator/eval_suite.py#L43). Background only: shows how the crash
  surfaces in the aggregate eval path. **Not modified.**
- **`tests/unit/test_faithfulness_checker.py`** — `class TestFaithfulnessChecker`, existing
  regression test `test_none_context_chunk_text`
  ([test_faithfulness_checker.py:231-242](tests/unit/test_faithfulness_checker.py#L231-L242)),
  which already reproduces the crash.


### Plan

Implementation steps :

1. In `rag/evaluator/faithfulness_checker.py`, at the context concatenation
   ([faithfulness_checker.py:34-36](rag/evaluator/faithfulness_checker.py#L34-L36)), replace
   `chunk.get("text", "")` with a null-safe coercion so a present-but-`None` value becomes
   `""` before the join i.e `chunk.get("text") or ""`. This is the only source change.
2. Run the existing regression test in isolation and confirm it now passes:
   `python -m pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -q`
3. Run the full faithfulness-checker test module to confirm no regressions — in particular
   that `test_missing_text_key_in_chunk` stays green:
   `python -m pytest tests/unit/test_faithfulness_checker.py -q`
4. Run the broader test suite to confirm nothing else is affected:
   `python -m pytest -q`

### Inputs & outputs

Representative inputs to `check(feedback, context_chunks)` and expected outputs after the
planned fix (`feedback = "Has Python skills"` throughout unless noted):

| Input `context_chunks` | Today | Expected after fix |
| --- | --- | --- |
| Valid text, e.g. `[{"text": "Strong Python skills demonstrated"}]` | valid float in `[0,1]` | **unchanged** — same float; valid scoring preserved |
| `[{"text": None}]` (the issue) | `TypeError` crash | valid float in `[0,1]`; the `None` chunk contributes no tokens (score `0.0` for this feedback/context) |
| Missing `text` key, e.g. `[{"content": "Python skills"}]` | valid float in `[0,1]` (default `""` applies) | **unchanged** — still a valid float |
| Mixed valid + `None`, e.g. `[{"text": "Python skills"}, {"text": None}]` | `TypeError` crash | valid float in `[0,1]`; scoring driven by the valid chunk, `None` ignored |

All outputs are a single `float` satisfying `0.0 <= score <= 1.0`.

### Risks & unknowns
- **Preserving valid scoring behavior.** The coercion must not change scores for valid
  chunks. Because the denominator is the number of *claims* (not chunks), a `None`/empty
  chunk contributing no tokens leaves valid-chunk scoring intact — this must be verified by
  the full module run.
- **Unexpected chunk shape.** The planned fix handles a valid chunk
  dictionary whose `text` value is `None`, but it does not handle a list element
  that is itself `None`. In that case, calling `chunk.get(...)` would raise
  `AttributeError` before the join operation. It is unclear whether this input
  shape can occur in production. It is however noteworthy.


### Edge cases

- **Empty string text** (`{"text": ""}`) — already handled today; contributes no tokens.
  Must remain a valid float after the fix.
- **Missing `text` key** (`{"content": ...}`) — default `""` applies; already valid and
  must stay valid.
- **All-`None` text values** (`[{"text": None}, {"text": None}]`) — after fix, yields an
  empty concatenated context → all claims unsupported → `0.0`.
- **Mixed valid and `None` text values** — after fix, scoring is driven by the valid chunk;
  `None` chunks are ignored.

