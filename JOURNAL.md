# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`FaithfulnessChecker.check()` builds the context string by calling
`chunk.get("text", "")` on each retrieved chunk. That default only applies when
the `"text"` key is missing entirely — if the key exists but is explicitly set
to `None`, `.get()` returns `None` instead of falling back to `""`. The
resulting list of chunk texts then gets passed to `" ".join(...)`, which
raises a `TypeError` because `join` requires every item to be a string. A
successful fix will coerce a `None` (or otherwise falsy/non-string) `"text"`
value to an empty string before joining, so a single malformed chunk no
longer crashes the whole evaluation run. This affects
`rag/evaluator/faithfulness_checker.py`.

**Branch name:** fix/153-faithfulness-checker-none-context-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ateressa/pathreview/commit/f7d5571

**Reproduction summary:**
Ran `pytest tests/unit/test_faithfulness_checker.py -k test_none_context_chunk_text`,
an existing test that calls `check()` with `context_chunks = [{"text": None}]`.
It fails with `TypeError: sequence item 0: expected str instance, NoneType found`,
raised from the `" ".join(...)` call in `FaithfulnessChecker.check()` — confirming
`chunk.get("text", "")` doesn't catch an explicit `None` value, only a missing key.

**PLAN.md link:** https://github.com/ateressa/pathreview/blob/fix/153-faithfulness-checker-none-context-text/PLAN.md

**Blockers or open questions:**
`relevance_scorer.py:32` has the same `chunk.get("text", "")` pattern and may have
an identical latent crash reachable through `EvalSuite.run()`. Leaving it out of
this issue's scope but may file a follow-up.
