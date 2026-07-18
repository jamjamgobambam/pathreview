## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker in the RAG evaluator (rag/evaluator/faithfulness_checker.py)
verifies that AI-generated claims are supported by retrieved context. It builds the
context string with chunk.get("text", ""), but .get() only falls back to the default
when the key is missing — if "text" exists with a value of None, it returns None, and
the " ".join(...) call raises a TypeError. Right now any chunk with a null text field
crashes the whole check instead of being handled. A successful fix treats None text
as an empty string (or skips the chunk) so the checker degrades gracefully, and makes
the failing test test_none_context_chunk_text pass.

**Selection notes:** Tier 1 fits my current familiarity with the codebase — the bug is
isolated to one function, has exact reproduction steps, and an existing failing test
defines "done," so the scope is well-bounded per the "Is this issue right for me?" checklist.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
