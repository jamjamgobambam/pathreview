## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `check()` method in `rag/evaluator/faithfulness_checker.py` builds
its context by calling `chunk.get("text", "")` on each context chunk,
assuming this will always yield a string. However, `.get()`'s default
value only kicks in when the key is missing entirely - if a chunk
dictionary has the key `"text"` present but explicitly set to `None`,
`.get()` returns `None` instead of the default empty string. This
`None` then gets passed into `" ".join(...)`, which raises a
`TypeError` since `join` expects a list of strings. A successful fix
will make the checker handle `None` values gracefully (coercing them
to empty strings before joining) so it can process context chunks
with missing or null text without crashing.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Scope-fit reasoning:**
I worked through the "Is this right for me?" checklist before claiming this issue.

- *Understanding the issue:* I can restate the bug without re-reading it -
  `check()` builds context via `chunk.get("text", "")`, but `.get()`'s default
  only applies when a key is missing, not when it's present with value `None`.
  A chunk with `{"text": None}` causes `" ".join(...)` to raise `TypeError`.
  "Done" means the checker returns a valid score instead of crashing when
  `text` is `None`.

- *Tier fit:* This is my first contribution to a codebase this size, so Tier 1
  is the right level - the fix is isolated to one function in one file and
  doesn't require understanding how the RAG pipeline fits together end to end.

- *Codebase readiness:* I located and read `check()` in
  `rag/evaluator/faithfulness_checker.py`, including the surrounding context
  needed to understand how chunks flow into the join call. I also read
  `tests/unit/test_faithfulness_checker.py` end to end, including
  `test_none_context_chunk_text` (text present but `None`) and the adjacent
  `test_missing_text_key_in_chunk` (text key missing entirely) - these are
  separate tests because they exercise different code paths even though both
  expect the checker to return a valid float score rather than crash.

- *Scope and time:* I checked the issue comments and the cohort ledger's
  Claims count for #153 and I'm comfortable with how many others are on it.
  This is a small, contained fix with a repro and existing tests already
  defined, so I estimate 3-6 hours of focused work is realistic within
  Weeks 8-9. There are no blockers or dependencies noted on the issue.


  ## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/Clearxheaded/pathreview/commit/5c8e0fd5e726ecdd0b598c0f3e9521f900a91e8a

**Reproduction summary:**
I reproduced the bug by calling `FaithfulnessChecker().check('Knows Python.', [{'text': None}])`
directly, which raised `TypeError: sequence item 0: expected str instance,
NoneType found` at the `" ".join(...)` call in `check()`. I also ran the
existing test suite and confirmed `test_none_context_chunk_text` fails with
the same error, while the adjacent `test_missing_text_key_in_chunk` already
passes - confirming the bug is specific to a `None` value, not a missing key.

**PLAN.md link:** https://github.com/Clearxheaded/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
None currently. Still deciding whether to search for similar `.get("text", ...)`
patterns elsewhere in the codebase during implementation, or keep scope
strictly limited to this one file for the Tier 1 fix.