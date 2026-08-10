## Solution plan

**Issue:** [Faithfulness checker crashes when a context chunk has `text: None`](https://github.com/ascherj/pathreview/issues/153)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

`check()` builds context text from chunks using `chunk.get("text", "")` at line 34 of `rag/evaluator/faithfulness_checker.py`. The default value `""` only applies when the key is missing from the dict. However,if `text` is present but explicitly set to `None`, `.get()` returns `None` as-is. The code then calls `" ".join([chunk.get("text", "") for chunk in context_chunks])`, which raises `TypeError: sequence item 0: expected str instance, NoneType found` because it tries to join `None` with a string. The expected behavior is that a chunk with `text: None` should be treated as empty content, contributing nothing to the joined context, rather than crashing the whole faithfulness check. Confirmed via both a manual repro and the project's existing (failing) test `test_none_context_chunk_text`.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- `rag/evaluator/faithfulness_checker.py`, line 34, inside `check()`:
  `context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])`
- `tests/unit/test_faithfulness_checker.py`, `test_none_context_chunk_text` (line 231), which currently asserts/exercises the crash, and needs to pass cleanly after the fix
- Possibly other files in `rag/evaluator/` if they share the same chunk retrieval pattern

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Change line 34 from `chunk.get("text", "")` to `chunk.get("text") or ""` so both a missing key and an explicit `None` normalize to an empty string
2. Run `test_none_context_chunk_text` to confirm it now passes
3. Run the full `test_faithfulness_checker.py` suite to confirm no regressions
4. Search `rag/evaluator/` for other instances of `.get("text", ...)` and apply the same fix if the pattern repeats elsewhere (the ones that i previously stated could share the same chunk retrieval pattern)
5. Run `make test-unit` and `make check` (lint/format/type-check) before committing the fix

### Inputs & outputs
What does your fix take as input? What should it produce or change?

Input: `context_chunks`, a list of dicts where each `text` value may be a non-empty string, an empty string, missing entirely, or `None`.
Output: `context_text`, a single joined string where `None`/missing-text chunks contribute an empty string instead of raising an exception.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- `chunk.get("text") or ""` also collapses any other false value (like an already-empty string) to the same empty-string behavior, which to me seems correct here, but worth confirming that no chunk legitimately needs to distinguish `None` from `""`. If so, I would have to pivot on my approach
- If chunks are arriving with `text: None` in the first place, that may point to a deeper issue upstream in ingestion producing malformed chunks, which makes it worthwhile to take a quick look at chunk construction to confirm closing this issue is an actual fix and not just a mask for a bigger issue.
- Haven't yet confirmed whether other evaluator files share the identical bug pattern; if they do, scope may expand slightly beyond the single line I noted above.

### Edge cases
What inputs or states should your fix handle gracefully?

- `{"text": None}`: the reported case, must not crash
- `{}`: missing key entirely, already handled by original code; confirm it still works after the fix
- `{"text": ""}`: already an empty string, should behave identically to the `None` case
- A mixed list with some `None` and some valid-text chunks: confirm only the `None` entries are neutralized, and valid text is preserved and correctly joined
