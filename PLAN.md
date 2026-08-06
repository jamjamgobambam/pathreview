## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None`
(https://github.com/ascherj/pathreview/issues/153)

### Understand
The root cause is a wrong assumption about how `dict.get` behaves. In
`FaithfulnessChecker.check`, the context chunks get flattened into one string with
`" ".join([chunk.get("text", "") for chunk in context_chunks])`. The `""` default
only fills in when the `"text"` key is missing. When a chunk is `{"text": None}`,
the key is present and its value is `None`, so `.get` returns `None`, and `join`
refuses to concatenate a `None` into a string.

Expected behavior is that a chunk carrying a null text value gets treated the same
as an empty or missing one, so the method returns a normal float score between 0.0
and 1.0. Actual behavior is that the whole call dies with
`TypeError: sequence item 0: expected str instance, NoneType found`, which means one
bad chunk can take down an entire faithfulness evaluation.

### Map
The fix is small and lives in the RAG evaluator.

- `rag/evaluator/faithfulness_checker.py` — the `check` method, specifically the
  context concatenation on line 34. This is the only production file I expect to
  change.
- `tests/unit/test_faithfulness_checker.py` — already contains
  `test_none_context_chunk_text` and `test_missing_text_key_in_chunk`, which are the
  tests that should go from failing to passing.

### Plan
1. Reproduce the crash with the existing `test_none_context_chunk_text` test and
   confirm it fails with the reported TypeError, which I have already done.
2. Change the comprehension so a null value collapses to an empty string. The
   smallest honest fix is `chunk.get("text") or ""`, which handles both a missing
   key and an explicit `None`.
3. Run the full faithfulness test file to confirm the two null and missing key tests
   pass and nothing else regressed.
4. Double check the returned score still lands in the 0.0 to 1.0 range for the null
   case, since an all empty context should mean no claims are supported.
5. Run the wider unit suite and the linter so the change is clean before I open a PR
   in Week 9.

### Inputs & outputs
The method takes a feedback string and a list of context chunk dicts. The fix
changes how one of those dicts is read. After the fix, a chunk shaped like
`{"text": None}` contributes an empty string to the joined context instead of
crashing, and `check` returns a valid float. Nothing about the scoring logic for
well formed chunks should change.

### Risks & unknowns
The main risk is that other places in the pipeline also read `chunk["text"]` or
`chunk.get("text", "")` and would still trip on a null value, so this fix might paper
over a data quality problem upstream rather than solve where the `None` comes from.
I want to grep the retriever and generator code to see whether null text should ever
reach the evaluator in the first place. A smaller unknown is whether a chunk could
arrive as something other than a dict, which the current code already assumes it will
not, and I do not plan to widen scope to cover that unless the tests ask for it.

### Edge cases
- A chunk with `text` set to `None`, which is the reported case.
- A chunk missing the `text` key entirely, covered by `test_missing_text_key_in_chunk`.
- A mix of good chunks and null chunks in the same list, where the good text should
  still count and the null one should quietly drop out.
- An empty string text value, which should behave the same as a null value.
- A context list where every chunk is null, which should return a low score rather
  than throw.
