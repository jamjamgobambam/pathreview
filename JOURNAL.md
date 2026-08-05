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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback was received before the end of the module. I checked the open pull request for comments and review activity, but no review was available during the Summer 2026 contribution period.

**How you responded:**
No response or additional code changes were required because no reviewer feedback was received.

---

### Reflection

**What was harder than you expected?**
The hardest part was designing a matching rule that fixed short claims without creating new false positives. Simply changing the required token overlap from two tokens to one allowed short technical claims such as `Knows Python` to pass, but it also caused contradictory statements like `well documented` and `poorly documented` to be treated as supported because they shared one generic token. I had to refine the solution by normalizing tokens, filtering generic words, and using an adaptive overlap threshold. I also spent more time than expected working through pre-commit checks, especially Ruff, Black, and mypy errors in the existing test file.

**What did you learn about working in a large codebase?**
I learned that a small code change can affect several existing assumptions and tests. In my own projects, I might change a threshold and move on after checking the main example, but in this repository I needed to understand the surrounding tests, contribution standards, type-checking rules, and existing behavior before deciding whether the fix was safe. I also learned to separate the main issue from unrelated failures, such as the `None` context-text error, and to document scope rather than assuming every nearby problem should be included. Working in someone else's codebase requires more attention to compatibility, conventions, and evidence that the change does not introduce regressions.

**How did AI tools help — and where did they fall short?**
AI tools were useful for explaining the existing token-overlap logic, identifying why short claims returned a score of `0.0`, drafting the initial `PLAN.md`, and suggesting test cases for punctuation, short technical claims, and generic-word false positives. They also helped me interpret Git and pre-commit output when commits failed. However, the first suggested implementation was too broad because accepting every one-token match caused false positives. I still needed to run the real test suite, inspect the exact failing inputs, and refine the rule based on the repository's behavior. This showed me that AI-generated code is a starting point, but it must be validated against actual tests and project conventions.

**What would you do differently if you started over?**
I would begin by writing a smaller set of focused regression tests before changing the implementation. In particular, I would test one supported short technical claim, one unsupported short claim, one punctuation case, and one generic-word false-positive case before selecting the final matching rule. I would also run `make check` and the pre-commit hooks earlier so that type annotation and formatting requirements did not appear near the end of the implementation process. Finally, I would avoid expanding the claim-extraction logic until I had confirmed that it was necessary for the issue.

**What are you most proud of from this module?**
I am most proud that I did not stop after making the original failing tests pass. When the first solution introduced a false positive, I used the additional test failure to improve the design instead of weakening or removing the test. The final work addressed the short-claim problem while preserving stricter behavior for longer or ambiguous claims, and I documented the full process from issue selection through reproduction, planning, implementation, testing, and PR submission.

---
