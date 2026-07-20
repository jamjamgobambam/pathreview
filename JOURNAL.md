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