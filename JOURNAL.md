# Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker` in the RAG evaluator (`rag/evaluator/faithfulness_checker.py`)
is supposed to score how well generated feedback is supported by the retrieved context
chunks. When one of those chunks has a `text` key whose value is `None`, the `check()`
method crashes with a `TypeError` instead of returning a score, because
`chunk.get("text", "")` only substitutes the default when the key is *missing* — not
when it is present with a `None` value — so `" ".join(...)` receives a `None`. Any
evaluation run that includes such a chunk breaks entirely rather than degrading
gracefully. A successful fix treats `None` text as an empty string so `check()` skips
the empty chunk and still returns a normal 0.0–1.0 faithfulness score, which is exactly
what the existing `test_none_context_chunk_text` unit test expects.

**Selection notes ("Is this right for me?"):**
This Tier 1 issue has a clear reproduction, a localized root cause in one evaluator,
and an existing regression test that defines success. It fits my scope because the fix
requires no API, schema, dependency, or architectural changes—only safe handling of a
nullable dictionary value. I can verify it by running the focused faithfulness checker
test and confirming `check()` returns a score instead of raising `TypeError`.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/wzltmp/pathreview/commit/7b62494

**Reproduction summary:**
I reproduced the issue against the `main` version of `rag/evaluator/faithfulness_checker.py`
by running `FaithfulnessChecker().check("Knows Python.", [{"text": None}])`. The observed
failure was `TypeError: sequence item 0: expected str instance, NoneType found` from the
`" ".join(...)` call that receives `None` from `chunk.get("text", "")`.

**PLAN.md link:** https://github.com/wzltmp/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** Not recorded yet

**Blockers or open questions:**
No current blockers. Before opening the PR, I still need to run the full required checks:
`make check` and `make test-unit`.
