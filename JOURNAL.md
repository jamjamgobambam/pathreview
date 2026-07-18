## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The faithfulness checker in the RAG evaluation layer
(`rag/evaluator/faithfulness_checker.py`) scores how well each claim in a
generated review is grounded in the retrieved context. Its `_is_supported()`
helper only counts a claim as supported when it shares at least two non-stopword
tokens with the context. Short factual claims like "Knows Python." overlap on
just one meaningful token even when the context fully supports them, so they are
always marked unsupported — a review made of short, well-grounded claims scores
0.0. A correct fix should let short but genuinely grounded claims be recognized
as supported (e.g. accepting a single strong token match, or a smarter matching
rule) without letting through claims that truly aren't in the context. This is
covered by the failing tests `test_partial_support_returns_middle_score`,
`test_multiple_context_chunks`, and `test_multiple_claims_varying_support` in
`tests/unit/test_faithfulness_checker.py`.

**Branch name:** fix/152-faithfulness-short-claims

**"Is this right for me?" reasoning:**
Tier 1, single-file scope in the RAG evaluator, which matches my prior RAG work.
The bug is a self-contained token-overlap threshold issue with three existing
failing unit tests, so I can reproduce it and verify a fix locally.

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
