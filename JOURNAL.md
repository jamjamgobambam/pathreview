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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/ascherj/pathreview/commit/e4af14567f9468c932572c9e72bbd08617af54cf)

**Reproduction summary:**
I reproduced Issue #152 by running `pytest tests/unit/test_faithfulness_checker.py -v`. The three tests associated with the issue—`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, and `test_multiple_claims_varying_support`—all failed consistently because the checker returned a faithfulness score of `0.0` and identified zero supported claims. The retrieved context contained the relevant technical terms, including Python, JavaScript, and Docker, but short claims with only one strong overlapping token were still classified as unsupported.

**PLAN.md link:** (https://github.com/ascherj/pathreview/commit/30ab1328f4b1c9dfb15efd43c6fcab4505ae533d)

**Blockers or open questions:**
I need to determine how `_is_supported()` can accept one-token matches for short, specific technical claims without allowing common or weak single-token matches to create false positives. The test suite also contains an unrelated existing failure involving a context chunk whose `text` value is `None`; I will keep that outside the scope of Issue #152 unless the maintainers indicate otherwise.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I reproduced Issue #152 and identified two related causes: short claims were
filtered out during claim extraction, and `_is_supported()` required at least
two meaningful token matches. I added a regression test based on the issue's
short-claim example and started updating claim extraction and token matching.

**Next steps:**
I will finish the implementation, add tests for short technical claims,
punctuation normalization, and generic-word false positives, then run
`make check` and `make test-unit`. After the targeted tests pass, I will open a
draft PR and request peer or mentor feedback.

**Blockers:**
The main risk is allowing one-token support without treating generic shared
words such as `project` or `experience` as sufficient evidence.

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/468)

**Branch:** `fix/152-faithfulness-short-claims`

**What you built:**
I updated the faithfulness checker so short, grounded claims can be recognized using an adaptive token-overlap rule. The implementation also normalizes punctuation, filters generic terms, and safely handles context chunks whose `text` value is `None`.

**Tests added or updated:**
I updated `tests/unit/test_faithfulness_checker.py` with regression tests for supported short claims, punctuation normalization, generic-word false positives, mixed supported and unsupported claims, and null context text.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

**Draft PR feedback received from:** none

**Peer review note:**
I requested feedback in Slack but did not receive a response before the submission deadline. I completed the self-review checklist and marked the PR ready for review.

---
