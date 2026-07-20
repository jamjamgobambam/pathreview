## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/153)

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [✅] Tier 1

**Problem summary:**
The FaithfulnessChecker in the RAG eval suite (rag/evaluator/faithfulness_checker.py) joins the text of every context chunk into one string using chunk.get("text", ""), which only guards against a missing key — not a chunk whose text is explicitly None. When a None-text chunk appears, the " ".join(...) call throws a TypeError and crashes the entire faithfulness check. A successful fix treats None text as empty so the checker skips it and keeps scoring the remaining chunks.

**Branch name:** fix/153-faithfulness-checker-none-chunk-text

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger