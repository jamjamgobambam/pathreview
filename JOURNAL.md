# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG evaluator's `FaithfulnessChecker` scores generated feedback by splitting it
into claims and checking whether each claim is backed by the retrieved context.
Two bugs in `rag/evaluator/faithfulness_checker.py` combine to make short,
factual claims unscoreable: `_extract_claims` discards any claim of 10
characters or fewer before it's even evaluated (e.g. "Knows SQL"), and
`_is_supported` requires a fixed minimum of two overlapping non-stopword
tokens between claim and context — a bar a one- or two-word claim can never
clear even when its single substantive word is fully present in the context.
The result is that short, clearly-supported claims are scored as unsupported,
dragging the faithfulness score down for reasons unrelated to actual
factual accuracy. A correct fix scores short claims on the strength of their
key terms rather than an absolute token count, so a claim like "Knows Python"
is recognized as supported when the context contains "Python".

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
