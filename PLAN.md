## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` — https://github.com/ascherj/pathreview/issues/153

### Understand
The root cause is `chunk.get("text", "")` in `check()`, which only substitutes
the default `""` when the `text` key is missing entirely. When a chunk is
`{"text": None}`, the key is present, so `.get()` returns `None` instead of
the default. Expected behavior: a chunk with no usable text should contribute
an empty string to the joined context. Actual behavior: `" ".join(...)`
raises `TypeError` because it can't join a `None` value with strings.

### Map
- `rag/evaluator/faithfulness_checker.py` — `FaithfulnessChecker.check()`,
  where the context string is built from chunk dicts.
- `tests/unit/test_faithfulness_checker.py` — contains
  `test_none_context_chunk_text`, the test that currently fails and defines
  expected behavior.

### Plan
1. Reproduce the crash locally and confirm `test_none_context_chunk_text` fails.
2. Change `chunk.get("text", "")` to `chunk.get("text") or ""` so both a
   missing key and an explicit `None` value normalize to an empty string.
3. Re-run the failing test and confirm it passes.
4. Run the full `test_faithfulness_checker.py` suite to confirm no regressions
   in the "missing key" case or normal text handling.
5. Commit the fix with a message referencing issue #153.

### Inputs & outputs
Input: a list of context chunk dicts passed to `check()`, where each chunk
may have a `text` key that is a string, missing, or `None`. Output: a single
joined context string used for the faithfulness comparison; the fix ensures
this join never raises regardless of which of those three states a chunk is in.

### Risks & unknowns
- Unsure why chunks with `text: None` are produced upstream in the first
  place (ingestion bug vs. expected null state) — this fix treats the
  symptom at the checker boundary rather than the unknown upstream cause.
- `or ""` also treats an empty string `""` and `None` identically, which is
  fine here but worth confirming no downstream logic distinguishes between
  "empty text" and "missing text."

### Edge cases
- `text` key missing entirely (the original `.get()` default case).
- `text` present but an empty string `""`.
- `chunk` itself is an empty dict `{}`.
- Non-string `text` value (e.g. a number or list) — out of scope for this
  fix, but worth flagging as a possible follow-up issue.