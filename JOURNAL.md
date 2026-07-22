## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The FaithfulnessChecker's `check()` method builds its context string from RAG
chunk dictionaries using `chunk.get("text", "")`, assuming this always returns
a string. But `.get()`'s default only applies when a key is missing — if a
chunk's `"text"` key exists but is explicitly set to `None`, `.get()` still
returns `None`, and the following `" ".join(...)` call then crashes with a
`TypeError` since you can't join a `None` value with strings. This lives in
`rag/evaluator/faithfulness_checker.py`, the part of the RAG evaluation
pipeline that checks whether AI-generated review claims are actually
supported by retrieved context. A successful fix would coerce a `None` text
value to an empty string before joining, so faithfulness checking degrades
gracefully instead of crashing whenever ingestion produces a chunk with
missing text content.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/vaishnavibollapalli/pathreview/commit/c762598

**Reproduction summary:**
Ran the existing test `test_none_context_chunk_text` in
`tests/unit/test_faithfulness_checker.py` and confirmed it fails with
`TypeError: sequence item 0: expected str instance, NoneType found` at line
34 of `rag/evaluator/faithfulness_checker.py`, where `chunk.get("text", "")`
returns `None` instead of the default when the chunk's `"text"` key is
explicitly `None`.

**PLAN.md link:** https://github.com/vaishnavibollapalli/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** [add Loom link here if you record one]

**Blockers or open questions:**
Still need to grep `ingestion/` and `agent/` to confirm whether the same
`.get("text", ...)` pattern appears elsewhere before finalizing the full fix
scope for Week 9.